plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.autoclicker.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.autoclicker.app"
        minSdk = 24
        targetSdk = 33
        versionCode = 5
        versionName = "1.4"
    }

    signingConfigs {
        create("stable") {
            storeFile = file("release.keystore")
            storePassword = "autoclicker"
            keyAlias = "autoclicker"
            keyPassword = "autoclicker"
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("stable")
        }
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("stable")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
}
