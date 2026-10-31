# Gera a MainActivity do Android com a "seta" (cursor) para controlar o player com o controle remoto da TV.
import json,os,sys
cfg=json.load(open('capacitor.config.json',encoding='utf-8'))
pkg=cfg['appId']
d='android/app/src/main/java/'+pkg.replace('.','/')
if not os.path.isdir(d): sys.exit('ERRO: pasta nao encontrada: '+d)
code='''package PKG;

import android.app.UiModeManager;
import android.content.Context;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
  // 0 = normal | 1 = player aberto (VOLTAR vai para o app) | 2 = seta ligada (setas/OK movem e clicam)
  private volatile int mode = 0;

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    getBridge().getWebView().addJavascriptInterface(new Ptr(), "AndroidPtr");
  }

  private void js(String code) {
    final WebView w = getBridge().getWebView();
    w.evaluateJavascript(code, null);
  }

  @Override
  public boolean dispatchKeyEvent(KeyEvent e) {
    int m = mode, k = e.getKeyCode();
    if (m >= 1 && k == KeyEvent.KEYCODE_BACK) {
      if (e.getAction() == KeyEvent.ACTION_UP) js("window.__back&&window.__back()");
      return true;
    }
    if (m == 2) {
      String d = null;
      if (k == KeyEvent.KEYCODE_DPAD_UP) d = "u";
      else if (k == KeyEvent.KEYCODE_DPAD_DOWN) d = "d";
      else if (k == KeyEvent.KEYCODE_DPAD_LEFT) d = "l";
      else if (k == KeyEvent.KEYCODE_DPAD_RIGHT) d = "r";
      else if (k == KeyEvent.KEYCODE_DPAD_CENTER || k == KeyEvent.KEYCODE_ENTER || k == KeyEvent.KEYCODE_NUMPAD_ENTER) d = "c";
      if (d != null) {
        if (e.getAction() == KeyEvent.ACTION_DOWN && (!d.equals("c") || e.getRepeatCount() == 0)) js("window.__ptr&&window.__ptr('" + d + "')");
        return true;
      }
    }
    return super.dispatchKeyEvent(e);
  }

  private class Ptr {
    @JavascriptInterface
    public boolean isTv() {
      UiModeManager u = (UiModeManager) getSystemService(Context.UI_MODE_SERVICE);
      PackageManager pm = getPackageManager();
      return (u != null && u.getCurrentModeType() == Configuration.UI_MODE_TYPE_TELEVISION)
          || pm.hasSystemFeature(PackageManager.FEATURE_LEANBACK)
          || !pm.hasSystemFeature(PackageManager.FEATURE_TOUCHSCREEN);
    }

    @JavascriptInterface
    public void mode(int m) { mode = m; }

    @JavascriptInterface
    public void tap(final float x, final float y) {
      if (mode != 2) return;
      runOnUiThread(new Runnable() {
        public void run() {
          final WebView w = getBridge().getWebView();
          float dn = getResources().getDisplayMetrics().density;
          final float px = x * dn, py = y * dn;
          final long t = SystemClock.uptimeMillis();
          MotionEvent a = MotionEvent.obtain(t, t, MotionEvent.ACTION_DOWN, px, py, 0);
          a.setSource(InputDevice.SOURCE_TOUCHSCREEN);
          w.dispatchTouchEvent(a);
          a.recycle();
          w.postDelayed(new Runnable() {
            public void run() {
              MotionEvent b = MotionEvent.obtain(t, SystemClock.uptimeMillis(), MotionEvent.ACTION_UP, px, py, 0);
              b.setSource(InputDevice.SOURCE_TOUCHSCREEN);
              w.dispatchTouchEvent(b);
              b.recycle();
            }
          }, 70);
        }
      });
    }
  }
}
'''.replace('PKG',pkg)
open(d+'/MainActivity.java','w',encoding='utf-8').write(code)
print('MainActivity (seta para TV) criada em',d)
