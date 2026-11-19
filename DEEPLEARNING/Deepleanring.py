import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs


### datasets importations
X,y=make_blobs(n_samples=100,n_features=2,centers=2,random_state=0)
y=y.reshape(y.shape[0],1)

print("dimension de x :", X.shape)
print("dimension y :",y.shape)
plt.scatter(X[:,0],X[:,1],c=y,cmap="summer")
plt.show()

from openalea.plantgl.all import *
cylinder = Cylinder(radius=0.5,height=1)
color=Material(Color3(0,255,0))
cylinder_shape=Shape(cylinder,color)


# function used to display coordonates x,y,z to enable or disable then 
Viewer.grids.setXYPlane(True)
Viewer.grids.setXZPlane(False)
Viewer.grids.setYZPlane(False)
Viewer.display(cylinder_shape)

# function of changing the background color of the viewer
Viewer.frameGL.setBgColor(255,255,255)
Viewer.frameGL.saveImage("cylinder.png")

# how to make a turtle shape with plantgl

turtle=PglTurtle()
for i in range(17):
    turtle.left(20).F(2)
scene=turtle.getScene()
Viewer.display(scene)

##### plantgl programming

