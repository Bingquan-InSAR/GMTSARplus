#!/usr/bin/env python
#
# part of pSAR to prvide some UI utilities 
# pSAR_impoygon.py has another solution for polygon or point selection based on
# an image show...
# developed by Wanpeng Feng, @NRCan, 2016-06-01
#
import numpy as np
import matplotlib
matplotlib.use('agg')
#
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import datetime
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pSAR
########################################
# plot time information
#
def dt_plot(dates,data):
    #
    timeshift = 5
    strudates = pSAR.ts.dates2dates(dates)
    #
    xmindate  = strudates[0]  + datetime.timedelta(days=-timeshift)
    xmaxdate  = strudates[-1] + datetime.timedelta(days=timeshift)
    # ymin      = np.min(data) - perpext
    # ymax      = np.max(data) + perpext
    #
    myFmt = mdates.DateFormatter('%Y-%m-%d')
    #
    plt.plot(strudates,data,'*',ms=15,color='red',label='Reference Acq.')
    #
    #
    ax = plt.gca()
    ax.set_xlim(xmindate,xmaxdate)
    #
    # ax.set_ylim(ymin,ymax)
    # ax.set_ylim(-200,200)
    #
    ax.xaxis.set_major_formatter(myFmt)
    ax.spines['bottom'].set_linewidth(2.5)
    ax.spines['left'].set_linewidth(2.5)
    ax.spines['top'].set_linewidth(2.5)
    ax.spines['right'].set_linewidth(2.5)
    #
    # Updated by Wanpeng Feng, @NRCan, 2017-02-02
    # The defaut direction of ticks were changed since matplotlib_v2.0. Now it is out in default.
    # I fixed the direction as "in" for baesline plot...
    #
    ax.tick_params('both', length=10, width=0.75, direction='in',which='major')

#
class Canvas(object):
    def __init__(self,ax):
        self.ax = ax
        #
        self.path, = ax.plot([],[],'o-',lw=3,color='yellow')
        self.vert = []
        # self.ax.set_title('LEFT: new point, MIDDLE: delete last point, RIGHT: close polygon')

        self.x = []
        self.y = []
        # print(self.mouse_button)
        self.mouse_button = {1: self._add_point, 2: self._delete_point, \
                             3: self._close_polygon}

    def set_location(self,event):
        if event.inaxes:
            self.x = event.xdata
            self.y = event.ydata

    def _add_point(self):
        self.vert.append((self.x,self.y))

    def _delete_point(self):
        if len(self.vert)>0:
            self.vert.pop()

    def _close_polygon(self):
        #self.vert.append(self.vert[0])
        return self.vert
    def update_path(self,event):

        # If the mouse pointer is not on the canvas, ignore buttons
        if not event.inaxes: return

        # Do whichever action correspond to the mouse button clicked
        self.mouse_button[event.button]()

        x = [self.vert[k][0] for k in range(len(self.vert))]
        y = [self.vert[k][1] for k in range(len(self.vert))]
        self.path.set_data(x,y)
        plt.draw()
#
def datashow(data,title='',showbar=True,ext=None,minv=-5,maxv=5,wrap=True,\
             cptname='RdYlBu',r=1,l=1,no=1,scale=2):
    #
    plt.subplot(l,r,no)
    if wrap:
       data = pSAR.roipac.wrap(data,minv=minv,maxv=maxv,scale=scale)
    #
    if ext is None:
       dims = data.shape
       ext  = [0,dims[1]-1,0,dims[0]-1]
    #
    if minv is None:
       minv = data[data!=0].min()
       maxv = data[data!=0].max()
    #   
    im = plt.imshow(data,vmin=minv,vmax=maxv,extent=ext,\
                    cmap=plt.get_cmap(cptname))
    plt.title(title)
    #
    if showbar==True:
      ax = plt.gca()
      divider = make_axes_locatable(ax)
      cax = divider.append_axes("right", size="5%", pad=0.05)
      cbar = plt.colorbar(im, cax=cax)
      #
      # significant change since matplotlib3.1
      # cbar.set_clim() will be deprecated.
      #
      plt.clim(minv,maxv)
    #
    return im
########################################
class pickup_points(object):
    def __init__(self,fig,out_loc_file):

        self.fig = fig
        self.out_loc_file = out_loc_file
        self.pid = []
        self.xs = []; # list(line.get_xdata())
        self.ys = []; # list(line.get_ydata())
        self.cid = fig.canvas.mpl_connect('button_press_event', self)

    def __call__(self, event):
        # print 'click', event
        outpoints = []
        if event.dblclick:
           # ids = self.pid;
           self.fig.canvas.mpl_disconnect(self.cid)
           #
           # output all picked locations into an ascii file
           #
           locs = np.array((self.xs,self.ys));
           locs = locs.T
           np.savetxt(self.out_loc_file, locs, fmt='%20.10f', \
                      delimiter=' ', newline='\n')
        else:
           #
           if event.button == 1:
              self.xs.append(event.xdata)
              self.ys.append(event.ydata)
              # self.plt_id.set_data(self.xs, self.ys)
              ix = event.xdata
              iy = event.ydata
              #
              outpoints = np.array([ix,iy])
              p_id = plt.plot(ix,iy,'o', ms=12, alpha=0.4,
                          color='yellow', visible=True)
              plt.draw()
              self.pid.append(p_id)
           #
        return outpoints

########################################
class draw_rect(object):
    def __init__(self):
        #
        self.ax      = plt.gca()
        self.x0      = None
        self.y0      = None
        self.x1      = None
        self.y1      = None
        #
        self.polyid  = []
        self.polyflag= 0
        self.pressid = 0
        self.x_index = [2,3]
        self.y_index = [1,2]
        self.poly_x  = np.array([self.x0,self.x0,self.x1,self.x1,self.x0])
        self.poly_y  = np.array([self.y0,self.y1,self.y1,self.y0,self.y0])
        self.polyid_active = 0
        self.npoly         = 0
        self.poly_m        = np.zeros((1,4))
        #self.ax.add_patch(self.rect)
        self.ax.figure.canvas.mpl_connect('button_press_event', \
                                          self.on_press)
        self.ax.figure.canvas.mpl_connect('button_release_event', \
                                          self.on_release)
        self.ax.figure.canvas.mpl_connect('motion_notify_event', \
                                          self.motion_notify_callback)

    def on_press(self, event):
        #
        # print(event.button)
        if event.button == 1:
           self.pressid = 1
           self.x0      = event.xdata
           self.y0      = event.ydata
           self.x1      = self.x0
           self.y1      = self.y0
           self.poly_x[:] = self.x0
           self.poly_y[:] = self.y0
           if self.polyflag == 1:
              self.polyid.set_xdata(self.poly_x)
              self.polyid.set_ydata(self.poly_y)
              plt.draw() 
           else:
              self.polyflag  = 1
              self.polyid,   = self.ax.plot(self.poly_x,self.poly_y,'o-r',\
                                            color='yellow',lw=3.5, alpha=0.85)
              plt.draw()
        elif event.button == 3:
           self.polyflag = 0
           self.npoly += 1
           if self.npoly == 1:
               self.poly_m = np.array([[np.min(self.poly_x),\
                                        np.max(self.poly_x),\
                                        np.min(self.poly_y),\
                                        np.max(self.poly_y)]])
           else:
               self.poly_m = np.append(self.poly_m,[[np.min(self.poly_x),\
                                                     np.max(self.poly_x),\
                                                     np.min(self.poly_y),\
                                                     np.max(self.poly_y)]],\
                                                     axis=0)
           #
        else:
           # print(dir(plt.Figure))
           # self.ax.show(block=False)
           print(dir(self.ax.figure))
           plt.close()
        #
        
    def on_release(self, event):
        #
        self.pressid = 0 
        return self
        #
    def motion_notify_callback(self,event):
        #
        if self.pressid == 1:
           x, y = event.xdata, event.ydata
           self.poly_x[self.x_index[0]] = x
           self.poly_x[self.x_index[1]] = x
           self.poly_y[self.y_index[0]] = y
           self.poly_y[self.y_index[1]] = y
           self.polyid.set_xdata(self.poly_x)
           self.polyid.set_ydata(self.poly_y)
           plt.draw()       


