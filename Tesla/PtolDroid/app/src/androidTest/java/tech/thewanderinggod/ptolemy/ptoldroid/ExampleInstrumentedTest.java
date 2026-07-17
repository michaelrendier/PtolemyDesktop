package tech.thewanderinggod.ptolemy.ptoldroid;

import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class ExampleInstrumentedTest {
    @Test
    public void useAppContext() {
        var appContext = InstrumentationRegistry.getInstrumentation().getTargetContext();
        assertEquals("tech.thewanderinggod.ptolemy.ptoldroid", appContext.getPackageName());
    }
}
