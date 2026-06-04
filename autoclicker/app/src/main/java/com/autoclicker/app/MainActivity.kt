package com.autoclicker.app

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import kotlin.math.roundToInt

class MainActivity : Activity() {

    private fun dp(v: Int): Int = (v * resources.displayMetrics.density).roundToInt()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0F1424"))
            setPadding(dp(24), dp(40), dp(24), dp(32))
        }

        // ---- Тақырып (иконка + атау) ----
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val icon = ImageView(this).apply {
            setImageResource(R.drawable.ic_mouse)
            layoutParams = LinearLayout.LayoutParams(dp(44), dp(44))
        }
        val titleBox = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(14), 0, 0, 0)
        }
        titleBox.addView(TextView(this).apply {
            text = "Авто Кликер"
            textSize = 26f
            setTextColor(Color.WHITE)
        })
        titleBox.addView(TextView(this).apply {
            text = "Рекламасыз • қарапайым"
            textSize = 13f
            setTextColor(Color.parseColor("#8A91A6"))
        })
        header.addView(icon)
        header.addView(titleBox)
        root.addView(header)

        // ---- Нұсқаулық картасы ----
        val card = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = roundedBg("#1B2235", dp(18))
            setPadding(dp(18), dp(16), dp(18), dp(16))
            val lp = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
            lp.topMargin = dp(24)
            layoutParams = lp
        }
        card.addView(TextView(this).apply {
            text = "Қолдану реті"
            textSize = 16f
            setTextColor(Color.WHITE)
            setPadding(0, 0, 0, dp(8))
        })
        card.addView(TextView(this).apply {
            text = "Төмендегі 3 қадамды рет-ретімен орындаңыз. Сосын экранда " +
                "ықшам панель шығады: тінтуір белгісін басатын жерге қойып, " +
                "ON басасыз."
            textSize = 14f
            setTextColor(Color.parseColor("#AEB4C7"))
            setLineSpacing(dp(3).toFloat(), 1f)
        })
        root.addView(card)

        // ---- Қадам түймелері ----
        root.addView(stepButton("1", "Overlay рұқсаты", "#2962FF") {
            startActivity(
                Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:$packageName")
                )
            )
        })
        root.addView(stepButton("2", "Accessibility қосу", "#2962FF") {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            Toast.makeText(
                this,
                "Тізімнен «Авто Кликер» қызметін тауып, қосыңыз",
                Toast.LENGTH_LONG
            ).show()
        })
        root.addView(stepButton("3", "Бастау", "#3DDC84") {
            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Алдымен Overlay рұқсатын беріңіз (1-түйме)", Toast.LENGTH_LONG).show()
                return@stepButton
            }
            val svc = Intent(this, OverlayService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(svc)
            } else {
                startService(svc)
            }
            Toast.makeText(this, "Панель экранда шықты", Toast.LENGTH_SHORT).show()
            moveTaskToBack(true)
        })

        root.addView(TextView(this).apply {
            text = "Жылдамдық: адамша (секундына ~5–15 рет)"
            textSize = 12f
            setTextColor(Color.parseColor("#6B7186"))
            gravity = Gravity.CENTER
            val lp = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
            lp.topMargin = dp(20)
            layoutParams = lp
        })

        val scroll = ScrollView(this).apply {
            setBackgroundColor(Color.parseColor("#0F1424"))
            addView(root)
        }
        setContentView(scroll)
    }

    /** Нөмірлі дөңгелек + мәтін бар әдемі түйме. */
    private fun stepButton(num: String, label: String, colorHex: String, onClick: () -> Unit): LinearLayout {
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            background = roundedBg(colorHex, dp(16))
            setPadding(dp(16), dp(16), dp(16), dp(16))
            isClickable = true
            setOnClickListener { onClick() }
            val lp = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
            lp.topMargin = dp(14)
            layoutParams = lp
        }
        val badge = TextView(this).apply {
            text = num
            textSize = 16f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            background = roundedBg("#33FFFFFF", dp(16))
            layoutParams = LinearLayout.LayoutParams(dp(32), dp(32))
        }
        val txt = TextView(this).apply {
            text = label
            textSize = 17f
            setTextColor(Color.WHITE)
            setPadding(dp(14), 0, 0, 0)
        }
        row.addView(badge)
        row.addView(txt)
        return row
    }

    private fun roundedBg(colorHex: String, radius: Int): GradientDrawable {
        return GradientDrawable().apply {
            shape = GradientDrawable.RECTANGLE
            cornerRadius = radius.toFloat()
            setColor(Color.parseColor(colorHex))
        }
    }
}
