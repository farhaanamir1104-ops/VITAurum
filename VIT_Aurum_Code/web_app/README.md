# VIT Aurum web app and Android APK

The web app is in `index.html`. It keeps the ledger in this browser/app's local storage; there is no account or cloud sync. A PIN is a convenience lock on this device, not a replacement for device encryption. The PWA shell can be cached for offline use after the first successful load. Google Fonts are optional and use system fallbacks offline.

## Run locally

Install Node.js 22 or newer, then in this folder:

```sh
npm install
npm run dev
```

Open the local URL printed by Vite. For a production web bundle, run `npm run build`; the deployable files are written to `dist/`. Host the site over HTTPS for PWA installation and service-worker support (localhost works for development). In Chrome on Android, open the HTTPS address and use **Install app** / **Add to Home screen**.

## Build an Android APK

1. Install Android Studio, including an Android SDK platform and Build Tools. Android Studio includes the JDK needed by its Gradle build.
2. In this folder, run:

   ```sh
   npm install
   npm run android:add
   npm run android:sync
   npm run android:open
   ```

   `android:add` creates the native Android project once. After that, skip it on later builds and use `npm run android:sync` before opening the project.
3. In Android Studio, wait for Gradle sync. Choose **Build > Build Bundle(s) / APK(s) > Build APK(s)**. The debug APK is normally at `android/app/build/outputs/apk/debug/app-debug.apk`.
4. For a shareable/release APK, use **Build > Generate Signed Bundle / APK > APK**, create and safely store a signing key, and complete the wizard. Keep that key private and backed up; future updates must use the same key.

For command-line debug builds after Android Studio has installed the SDK:

```sh
cd android
./gradlew assembleDebug
```

The result is `android/app/build/outputs/apk/debug/app-debug.apk`. If Gradle reports that SDK/JDK tools are missing, install them in Android Studio's SDK Manager and set `ANDROID_HOME`/`JAVA_HOME` for your shell.

## App identity and data

The Capacitor app ID is `com.vitaurum.ledger` in `capacitor.config.json`. Set it to a unique reverse-domain ID before publishing; changing it later makes Android treat the app as a different app. Web browser data and APK data are separate local stores. Export a backup from the app before switching devices or packaging a new installation, and restore it inside the new app.
