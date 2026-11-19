package com.giftmanager.app;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class MainActivity extends Activity {
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        webView.setWebViewClient(new WebViewClient());

        // Chaquopy 的 Python 解释器需要在APP启动时初始化一次
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        try {
            prepareFiles();
        } catch (IOException e) {
            throw new RuntimeException("初始化数据失败", e);
        }

        File filesDir = getFilesDir();
        String baseDir = new File(filesDir, "www").getAbsolutePath();
        String dbPath = new File(filesDir, "gift").getAbsolutePath();

        Python py = Python.getInstance();
        int port = py.getModule("mobile_entry")
                     .callAttr("start", baseDir, dbPath)
                     .toInt();

        webView.loadUrl("http://127.0.0.1:" + port + "/");
    }

    /** 把随包资源解包到应用私有目录：静态文件每次覆盖，数据库仅在首次创建。 */
    private void prepareFiles() throws IOException {
        File filesDir = getFilesDir();
        File www = new File(filesDir, "www");
        if (!www.exists()) www.mkdirs();

        copyAsset("index.html", new File(www, "index.html"), true);
        copyAsset("gift", new File(filesDir, "gift"), false);
    }

    private void copyAsset(String asset, File dest, boolean overwrite) throws IOException {
        if (dest.exists() && !overwrite) return;
        try (InputStream in = getAssets().open(asset);
             OutputStream out = new FileOutputStream(dest)) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
        }
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
