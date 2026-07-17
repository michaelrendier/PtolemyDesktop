package tech.thewanderinggod.ptolemy.ptoldroid;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;

/**
 * PtolDroid — Ptolemy Android client (Tesla Face / device interfacing)
 * Interfaces with Tesla.HolePunch and Tesla.KVM over punched UDP socket.
 */
public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }
}
