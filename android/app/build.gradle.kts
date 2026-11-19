import java.io.File

plugins {
    id("com.android.application")
    id("com.chaquo.python")
}

// 把项目根目录的后端与前端资源同步进 Android 工程，避免维护两份副本。
// 放在配置阶段执行，确保 Chaquopy 在扫描源码前 app.py 已就位。
val projectRoot = file("../../")
val pythonDir = file("src/main/python")
val assetsDir = file("src/main/assets")

pythonDir.mkdirs()
assetsDir.mkdirs()
File(projectRoot, "app.py").copyTo(File(pythonDir, "app.py"), overwrite = true)
File(projectRoot, "index.html").copyTo(File(assetsDir, "index.html"), overwrite = true)
File(projectRoot, "gift").copyTo(File(assetsDir, "gift"), overwrite = true)

android {
    namespace = "com.giftmanager.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.giftmanager.app"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
        }
    }

    // APK 输出文件名统一为「礼记.apk」（仅 debug，避免多渠道/多构建类型重名冲突）
    applicationVariants.all {
        if (name == "debug") {
            outputs.all {
                (this as com.android.build.gradle.internal.api.ApkVariantOutputImpl)
                    .outputFileName = "礼记.apk"
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
}

chaquopy {
    defaultConfig {
        version = "3.11"
        android.defaultConfig.ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }
}
