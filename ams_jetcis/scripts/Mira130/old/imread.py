import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
img = np.fromfile("record_tmp.raw", dtype=np.uint16)
w=1088
h=1280
img = img.reshape(h,w)

img = img[0:self.h, 0:self.w]
f = "{}_{}.tiff".format('jef', 1)
Image.fromarray(img*64).save(f)
plt.imshow(img)
plt.show()