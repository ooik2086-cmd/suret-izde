package com.autoclicker.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import kotlin.math.roundToInt

/**
 * Экран үстіндегі қалқымалы басқару:
 *  - тінтуір белгісі (сүйреп жылжытуға болады) — басу осы жерге түседі
 *  - басқару панелі: ◀ ▶ (жылжыту), – + (жылдамдық), СТАРТ/СТОП, ✕ (жабу)
 */
class OverlayService : Service() {

    private lateinit var windowManager: WindowManager

    private lateinit var targetView: ImageView
    private lateinit var targetParams: WindowManager.LayoutParams

    private lateinit var panelView: LinearLayout
    private lateinit var panelParams: WindowManager.LayoutParams
    private lateinit var speedLabel: TextView
    private lateinit var startStopButton: Button

    private val handler = Handler(Looper.getMainLooper())
    private var running = false

    // Интервал нұсқалары (ms): баяудан жылдамға дейін.
    // 2000ms = 2с сайын 1 рет ... 10ms = ~секундына 100 рет
    private val intervals = longArrayOf(2000, 1000, 500, 200, 100, 50, 20, 10)
    private var intervalIndex = 2 // 500ms ≈ секундына 2 рет

    private val clickRunnable = object : Runnable {
        override fun run() {
            if (!running) return
            val svc = AutoClickService.instance
            if (svc != null) {
                val x = (targetParams.x + targetView.width / 2).toFloat()
                val y = (targetParams.y + targetView.height / 2).toFloat()
                svc.click(x, y)
            }
            handler.postDelayed(this, intervals[intervalIndex])
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        startAsForeground()
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        addTargetView()
        addPanelView()
    }

    private fun overlayType(): Int =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE

    private fun addTargetView() {
        targetView = ImageView(this).apply {
            setImageResource(R.drawable.ic_mouse)
        }
        targetParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            overlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 300
            y = 600
        }

        targetView.setOnTouchListener(object : View.OnTouchListener {
            private var initX = 0
            private var initY = 0
            private var touchX = 0f
            private var touchY = 0f
            override fun onTouch(v: View?, event: MotionEvent): Boolean {
                if (running) return false
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = targetParams.x
                        initY = targetParams.y
                        touchX = event.rawX
                        touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        targetParams.x = initX + (event.rawX - touchX).roundToInt()
                        targetParams.y = initY + (event.rawY - touchY).roundToInt()
                        windowManager.updateViewLayout(targetView, targetParams)
                        return true
                    }
                }
                return false
            }
        })

        windowManager.addView(targetView, targetParams)
    }

    private fun addPanelView() {
        panelView = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setBackgroundColor(Color.parseColor("#CC000000"))
            setPadding(8, 8, 8, 8)
        }

        speedLabel = TextView(this).apply {
            setTextColor(Color.WHITE)
            textSize = 12f
            setPadding(12, 0, 12, 0)
            gravity = Gravity.CENTER
        }

        startStopButton = smallButton("СТАРТ") { toggleRun() }

        panelView.addView(smallButton("◀") { moveTarget(-40) })
        panelView.addView(smallButton("▶") { moveTarget(40) })
        panelView.addView(smallButton("–") { changeSpeed(-1) })
        panelView.addView(speedLabel)
        panelView.addView(smallButton("+") { changeSpeed(1) })
        panelView.addView(startStopButton)
        panelView.addView(smallButton("✕") { stopSelf() })

        updateSpeedLabel()

        panelParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            overlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 0
            y = 0
        }

        windowManager.addView(panelView, panelParams)
    }

    private fun smallButton(label: String, onClick: () -> Unit): Button {
        return Button(this).apply {
            text = label
            textSize = 13f
            setPadding(6, 4, 6, 4)
            minWidth = 0
            minimumWidth = 0
            setOnClickListener { onClick() }
        }
    }

    private fun moveTarget(dx: Int) {
        targetParams.x += dx
        windowManager.updateViewLayout(targetView, targetParams)
    }

    private fun changeSpeed(dir: Int) {
        intervalIndex = (intervalIndex + dir).coerceIn(0, intervals.size - 1)
        updateSpeedLabel()
    }

    private fun updateSpeedLabel() {
        val ms = intervals[intervalIndex]
        val perSec = 1000.0 / ms
        val rate = if (perSec >= 1) "${perSec.roundToInt()}/сек" else "${ms / 1000.0}с"
        speedLabel.text = "$ms ms\n$rate"
    }

    private fun toggleRun() {
        if (AutoClickService.instance == null) {
            Toast.makeText(
                this,
                "Accessibility қызметін қосыңыз (2-түйме)!",
                Toast.LENGTH_LONG
            ).show()
            return
        }
        running = !running
        if (running) {
            startStopButton.text = "СТОП"
            // Тап белгінің астындағы ойынға өтуі үшін белгіні басылмайтын етеміз.
            targetParams.flags = targetParams.flags or
                WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
            windowManager.updateViewLayout(targetView, targetParams)
            handler.post(clickRunnable)
        } else {
            startStopButton.text = "СТАРТ"
            handler.removeCallbacks(clickRunnable)
            targetParams.flags = targetParams.flags and
                WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
            windowManager.updateViewLayout(targetView, targetParams)
        }
    }

    private fun startAsForeground() {
        val channelId = "autoclicker"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Авто Кликер",
                NotificationManager.IMPORTANCE_LOW
            )
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(channel)
        }
        val notification: Notification =
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                Notification.Builder(this, channelId)
                    .setContentTitle("Авто Кликер")
                    .setContentText("Қосулы")
                    .setSmallIcon(R.drawable.ic_mouse)
                    .build()
            } else {
                @Suppress("DEPRECATION")
                Notification.Builder(this)
                    .setContentTitle("Авто Кликер")
                    .setContentText("Қосулы")
                    .setSmallIcon(R.drawable.ic_mouse)
                    .build()
            }
        startForeground(1, notification)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        running = false
        handler.removeCallbacks(clickRunnable)
        if (this::targetView.isInitialized) {
            runCatching { windowManager.removeView(targetView) }
        }
        if (this::panelView.isInitialized) {
            runCatching { windowManager.removeView(panelView) }
        }
    }
}
