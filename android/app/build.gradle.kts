import java.io.File

plugins {
    id("com.android.application")
    id("com.chaquo.python")
}

// 把项目根目录的后端与前端资源同步进 Android 工程，避免维护两份副本。
// 放在配置阶段执行，确保 Chaquopy 在扫描源码前 app.py / server 包已就位。
val projectRoot = file("../../")
val pythonDir = file("src/main/python")
val assetsDir = file("src/main/assets")

pythonDir.mkdirs()
assetsDir.mkdirs()
File(projectRoot, "app.py").copyTo(File(pythonDir, "app.py"), overwrite = true)
File(projectRoot, "server").copyRecursively(File(pythonDir, "server"), overwrite = true)
// 前端页面在 templates/ 下，样式与脚本在 static/ 下，按目录整体同步
File(projectRoot, "templates").copyRecursively(File(assetsDir, "templates"), overwrite = true)
File(projectRoot, "static").copyRecursively(File(assetsDir, "static"), overwrite = true)
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

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
}

chaquopy {
    defaultConfig {
        version = "3.11"
        // peewee 是纯 Python ORM，无 C 扩展，Chaquopy 可直接安装
        pip {
            install("peewee==4.5.3")
        }
        android.defaultConfig.ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }
}
