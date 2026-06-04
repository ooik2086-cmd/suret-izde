package com.autoclicker.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import kotlin.math.roundToInt

/**
 * Экран үстіндегі басқару:
 *  - тінтуір белгісі (саусақпен қалаған жерге сүйреледі) — басу осы жерге түседі
 *  - тік (вертикаль) панель: басылу саны, СТАРТ, СТОП, ✕ (жабу)
 *  - панельді жоғарғы тұтқасынан ұстап кез келген жерге жылжытуға болады
 *  - жылдамдық: секундына 1 рет
 */
class OverlayService : Service() {

    private lateinit var windowManager: WindowManager

    private lateinit var targetView: ImageView
    private lateinit var targetParams: WindowManager.LayoutParams

    private lateinit var panelView: LinearLayout
    private lateinit var panelParams: WindowManager.LayoutParams
    private lateinit var counterLabel: TextView

    private val handler = Handler(Looper.getMainLooper())
    private var running = false
    private var clickCount = 0

    private val intervalMs = 1000L // секундына 1 рет

    private val clickRunnable = object : Runnable {
        override fun run() {
            if (!running) return
            val svc = AutoClickService.instance
            if (svc != null) {
                val x = (targetParams.x + targetView.width / 2).toFloat()
                val y = (targetParams.y + targetView.height / 2).toFloat()
                svc.click(x, y)
                clickCount++
                counterLabel.text = "Басылды: $clickCount"
            }
            handler.postDelayed(this, intervalMs)
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

    private fun dp(v: Int): Int = (v * resources.displayMetrics.density).roundToInt()

    // ---- Тінтуір белгісі (басу нысанасы) ----
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
            x = dp(150)
            y = dp(350)
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

    // ---- Басқару панелі (тік) ----
    private fun addPanelView() {
        panelView = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(10), dp(16), dp(16))
            background = roundedBg("#EE1E2230", dp(22))
        }

        // Жоғарғы тұтқа: «жылжыту» + ✕
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val dragHint = TextView(this).apply {
            text = "⠿  жылжыту"
            setTextColor(Color.parseColor("#9AA0B4"))
            textSize = 13f
        }
        val spacer = View(this).apply {
            layoutParams = LinearLayout.LayoutParams(0, 1, 1f)
        }
        val closeBtn = TextView(this).apply {
            text = "✕"
            setTextColor(Color.WHITE)
            textSize = 20f
            setPadding(dp(14), dp(2), dp(6), dp(6))
            setOnClickListener { stopSelf() }
        }
        header.addView(dragHint)
        header.addView(spacer)
        header.addView(closeBtn)

        // Басылу саны
        counterLabel = TextView(this).apply {
            text = "Басылды: 0"
            setTextColor(Color.WHITE)
            textSize = 20f
            setPadding(0, dp(10), 0, dp(2))
        }
        val rateLabel = TextView(this).apply {
            text = "Жылдамдық: секундына 1 рет"
            setTextColor(Color.parseColor("#9AA0B4"))
            textSize = 13f
            setPadding(0, 0, 0, dp(14))
        }

        val startBtn = bigButton("СТАРТ", "#3DDC84") { startClicking() }
        val stopBtn = bigButton("СТОП", "#FF5252") { stopClicking() }

        panelView.addView(header)
        panelView.addView(counterLabel)
        panelView.addView(rateLabel)
        panelView.addView(startBtn)
        panelView.addView(spaceView(dp(12)))
        panelView.addView(stopBtn)

        panelParams = WindowManager.LayoutParams(
            dp(230),
            WindowManager.LayoutParams.WRAP_CONTENT,
            overlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = dp(20)
            y = dp(90)
        }

        attachDrag(header)

        windowManager.addView(panelView, panelParams)
    }

    /** Панельді тұтқасынан ұстап жылжыту. */
    private fun attachDrag(handle: View) {
        handle.setOnTouchListener(object : View.OnTouchListener {
            private var initX = 0
            private var initY = 0
            private var touchX = 0f
            private var touchY = 0f
            override fun onTouch(v: View?, event: MotionEvent): Boolean {
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        initX = panelParams.x
                        initY = panelParams.y
                        touchX = event.rawX
                        touchY = event.rawY
                        return true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        panelParams.x = initX + (event.rawX - touchX).roundToInt()
                        panelParams.y = initY + (event.rawY - touchY).roundToInt()
                        windowManager.updateViewLayout(panelView, panelParams)
                        return true
                    }
                }
                return false
            }
        })
    }

    private fun bigButton(label: String, colorHex: String, onClick: () -> Unit): Button {
        return Button(this).apply {
            text = label
            textSize = 17f
            setTextColor(Color.WHITE)
            isAllCaps = false
            background = roundedBg(colorHex, dp(14))
            stateListAnimator = null
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dp(54)
            )
            setOnClickListener { onClick() }
        }
    }

    private fun spaceView(h: Int): View = View(this).apply {
        layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, h)
    }

    private fun roundedBg(colorHex: String, radius: Int): GradientDrawable {
        return GradientDrawable().apply {
            shape = GradientDrawable.RECTANGLE
            cornerRadius = radius.toFloat()
            setColor(Color.parseColor(colorHex))
        }
    }

    private fun startClicking() {
        if (AutoClickService.instance == null) {
            Toast.makeText(
                this,
                "Accessibility қызметін қосыңыз (2-түйме)!",
                Toast.LENGTH_LONG
            ).show()
            return
        }
        if (running) return
        running = true
        clickCount = 0
        counterLabel.text = "Басылды: 0"
        // Тап нысананың астындағы ойынға өтуі үшін белгіні басылмайтын етеміз
        targetParams.flags = targetParams.flags or
            WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
        windowManager.updateViewLayout(targetView, targetParams)
        handler.post(clickRunnable)
    }

    private fun stopClicking() {
        if (!running) return
        running = false
        handler.removeCallbacks(clickRunnable)
        targetParams.flags = targetParams.flags and
            WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE.inv()
        windowManager.updateViewLayout(targetView, targetParams)
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
