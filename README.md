set NOSE_TIMEOUT env variable and enjoy!


Also with the ability to put specific timeout per test method

```python
import time
import unittest
from nose.plugins.attrib import attr


class TestWhatever(unittest.TestCase):
    @attr(timeout=5)
    def test_01(self):
        time.sleep(1000)

    def test_02(self):
        time.sleep(1000)
```


```bash
nosetests --with-timeout --timeout=20
# first test would timeout after 5sec, and second one after 20sec
```
