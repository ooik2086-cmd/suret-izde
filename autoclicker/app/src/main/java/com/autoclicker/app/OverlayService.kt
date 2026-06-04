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
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import kotlin.math.abs
import kotlin.math.roundToInt

/**
 * Ықшам тік панель — экранның шетінде тұрады, көп орын алмайды.
 * Реті (жоғарыдан төмен): ⠿ жылжыту, ON (жасыл), OFF (қызыл), сан, ✕ (қызыл).
 * Жылдамдық: секундына 1 рет.
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

    private var panelWidthPx = 0
    private var screenWidthPx = 0

    private val clickRunnable = object : Runnable {
        override fun run() {
            if (!running) return
            val svc = AutoClickService.instance
            if (svc != null) {
                val x = (targetParams.x + targetView.width / 2).toFloat()
                val y = (targetParams.y + targetView.height / 2).toFloat()
                svc.click(x, y)
                clickCount++
                counterLabel.text = clickCount.toString()
            }
            handler.postDelayed(this, intervalMs)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        startAsForeground()
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        screenWidthPx = resources.displayMetrics.widthPixels
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
            x = dp(130)
            y = dp(400)
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

    // ---- Ықшам тік панель ----
    private fun addPanelView() {
        panelWidthPx = dp(74)

        panelView = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(8), dp(8), dp(8), dp(10))
            background = roundedBg("#EE1E2230", dp(22))
        }

        // 1) Жылжыту тұтқасы (⠿)
        val dragHandle = TextView(this).apply {
            text = "⠿"
            setTextColor(Color.parseColor("#9AA0B4"))
            textSize = 22f
            gravity = Gravity.CENTER
            setPadding(dp(6), dp(2), dp(6), dp(8))
        }

        // 2) ON (жасыл)
        val onBtn = squareButton("ON", "#3DDC84", 15f) { startClicking() }
        // 3) OFF (қызыл)
        val offBtn = squareButton("OFF", "#FF5252", 14f) { stopClicking() }

        // 4) Басылу саны
        counterLabel = TextView(this).apply {
            text = "0"
            setTextColor(Color.WHITE)
            textSize = 19f
            gravity = Gravity.CENTER
            setPadding(0, dp(8), 0, dp(2))
        }
        val likeLabel = TextView(this).apply {
            text = "басылды"
            setTextColor(Color.parseColor("#9AA0B4"))
            textSize = 10f
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, dp(8))
        }

        // 5) ✕ (қызыл)
        val closeBtn = squareButton("✕", "#E53935", 18f) { stopSelf() }

        panelView.addView(dragHandle)
        panelView.addView(onBtn)
        panelView.addView(spaceView(dp(10)))
        panelView.addView(offBtn)
        panelView.addView(counterLabel)
        panelView.addView(likeLabel)
        panelView.addView(closeBtn)

        panelParams = WindowManager.LayoutParams(
            panelWidthPx,
            WindowManager.LayoutParams.WRAP_CONTENT,
            overlayType(),
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = screenWidthPx - panelWidthPx - dp(6) // оң шетте
            y = dp(140)
        }

        attachDrag(dragHandle)

        windowManager.addView(panelView, panelParams)
    }

    /** Панельді тұтқасынан ұстап жылжыту + жібергенде ең жақын шетке жабысу. */
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
                    MotionEvent.ACTION_UP -> {
                        // ең жақын шетке жабыстыру
                        val center = panelParams.x + panelWidthPx / 2
                        panelParams.x = if (center < screenWidthPx / 2) dp(6)
                            else screenWidthPx - panelWidthPx - dp(6)
                        windowManager.updateViewLayout(panelView, panelParams)
                        return true
                    }
                }
                return false
            }
        })
    }

    private fun squareButton(label: String, colorHex: String, size: Float, onClick: () -> Unit): TextView {
        return TextView(this).apply {
            text = label
            textSize = size
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            background = roundedBg(colorHex, dp(14))
            layoutParams = LinearLayout.LayoutParams(dp(58), dp(46))
            isClickable = true
            setOnClickListener { onClick() }
        }
    }

    private fun spaceView(h: Int): View = View(this).apply {
        layoutParams = LinearLayout.LayoutParams(dp(1), h)
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
        counterLabel.text = "0"
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
