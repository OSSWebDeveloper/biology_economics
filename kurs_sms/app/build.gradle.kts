import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

// Imzo kaliti. `kalit.properties` bo'lmasa, release ham debug kaliti bilan
// imzolanadi - APK baribir o'rnatiladi, lekin yangilash uchun doimiy kalit yaxshiroq.
val kalitFayl = rootProject.file("kalit.properties")
val kalitSozlama = Properties().apply {
    if (kalitFayl.exists()) kalitFayl.inputStream().use { load(it) }
}


// Versiya bitta joydan olinadi: loyiha ildizidagi `versiya.txt`.
// Saytdagi (`bio_moliya\versiya.txt`) bilan bir xil uslub.
val versiya: String = rootProject.file("versiya.txt")
    .takeIf { it.exists() }?.readText()?.trim()?.ifBlank { null } ?: "1.0.0"

// "1.2.3" -> 10203 (har bir bo'lak ikki xonagacha)
val versiyaRaqami: Int = versiya.split(".")
    .map { it.filter(Char::isDigit).toIntOrNull() ?: 0 }
    .let { (it + listOf(0, 0, 0)).take(3) }
    .let { (katta, orta, kichik) -> katta * 10000 + orta * 100 + kichik }

android {
    namespace = "uz.olimjonov.kurssms"
    compileSdk = 35

    defaultConfig {
        applicationId = "uz.olimjonov.kurssms"
        minSdk = 24
        targetSdk = 35
        versionCode = versiyaRaqami
        versionName = versiya
        resourceConfigurations += listOf("en")
        // Ilova ichida ko'rsatish uchun
        buildConfigField("String", "VERSIYA", "\"$versiya\"")
    }

    signingConfigs {
        if (kalitFayl.exists()) {
            create("chiqarish") {
                storeFile = rootProject.file(kalitSozlama.getProperty("storeFile"))
                storePassword = kalitSozlama.getProperty("storePassword")
                keyAlias = kalitSozlama.getProperty("keyAlias")
                keyPassword = kalitSozlama.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
        }
        release {
            isMinifyEnabled = false
            if (kalitFayl.exists()) {
                signingConfig = signingConfigs.getByName("chiqarish")
            }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.work:work-runtime-ktx:2.9.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")

    implementation(platform("androidx.compose:compose-bom:2024.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    debugImplementation("androidx.compose.ui:ui-tooling")
}
