package com.autoclicker.app

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 64, 48, 48)
            setBackgroundColor(Color.WHITE)
        }

        val title = TextView(this).apply {
            text = "Авто Кликер"
            textSize = 26f
            setTextColor(Color.parseColor("#1976D2"))
        }
        root.addView(title)

        val info = TextView(this).apply {
            text = "\nҚолдану реті:\n" +
                "1) Overlay (экран үстінен) рұқсатын беріңіз\n" +
                "2) Accessibility қызметін қосыңыз\n" +
                "3) «Бастау» түймесін басыңыз\n\n" +
                "Экранда тінтуір белгісі шығады. Оны қалаған жерге сүйреп қойыңыз, " +
                "панельден жылдамдықты таңдап, СТАРТ басыңыз.\n"
            textSize = 16f
            setTextColor(Color.DKGRAY)
        }
        root.addView(info)

        root.addView(makeButton("1. Overlay рұқсаты") {
            startActivity(
                Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:$packageName")
                )
            )
        })

        root.addView(makeButton("2. Accessibility қосу") {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            Toast.makeText(
                this,
                "Тізімнен «Авто Кликер» қызметін тауып, қосыңыз",
                Toast.LENGTH_LONG
            ).show()
        })

        root.addView(makeButton("3. Бастау") {
            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Алдымен Overlay рұқсатын беріңіз (1-түйме)", Toast.LENGTH_LONG).show()
                return@makeButton
            }
            val svc = Intent(this, OverlayService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(svc)
            } else {
                startService(svc)
            }
            Toast.makeText(this, "Тінтуір белгісі экранда шықты", Toast.LENGTH_SHORT).show()
            moveTaskToBack(true)
        })

        val scroll = ScrollView(this)
        scroll.addView(root)
        setContentView(scroll)
    }

    private fun makeButton(label: String, onClick: () -> Unit): Button {
        return Button(this).apply {
            text = label
            textSize = 16f
            val lp = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
            lp.topMargin = 24
            layoutParams = lp
            setOnClickListener { onClick() }
        }
    }
}
