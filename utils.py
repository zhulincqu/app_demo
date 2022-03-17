from copyreg import dispatch_table
from dis import dis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging


        
def normalize(x):
    """
    Normalize 1d array using max-min way
    """
    x = np.asarray(x)
    return (x - x.min()) / (np.ptp(x))


def shirley_baseline(dat, limits=None, maxit = 50, err = 1e-6, display=False):
    ''' 
    Function calculates the Shirley background 
    following Bruckner's approach. The background 
    is calculated iteratively and then subtracted from the dataset.
    
    Args:
      dat (np.array): matrix with x in first col (x = dat[:,0]) and y in the second col (y=dat[:,1])
      limits: spectrum limits ()
      maxit: maximum number of iterations
      err: cut-off error
      
    Returns:
      Tuple(baseline, corrected): (proposed baseline, baseline corrected spectra.
      
    '''
    
    x = np.array(dat[:, 0])
    y = np.array(dat[:, 1]) 
    
    if limits is None:
        pass
    else:
        xid1=np.where(np.round(x)==max(limits))[0][0]
        xid2=np.where(np.round(x)==min(limits))[0][0]
        # crop between x-condition limits 
        x=x[xid1:(xid2+1)]
        y=y[xid1:(xid2+1)]

    npts=len(y)
    limsy=np.array([y[0],y[npts-1]])
    lowlim = np.min(limsy)
    # Intial constant background  
    BGND = np.repeat(lowlim, npts)
    SumBGND = np.sum(BGND)
    SumRTF = np.sum(y)  
    RangeY = np.diff(list(reversed(limsy)))
    logging.info(f"RangeY is {RangeY}")
    
    if  np.diff(limsy) > 0:
        nloop = 0
        while nloop < maxit:
            nloop = nloop + 1
            for idx in list(reversed(range(npts))):
                # print((npts-idx-1),BGND[npts-idx-1])
                BGND[npts-idx-1] = ((RangeY/(SumRTF-np.sum(BGND)))*
                    (np.sum(y[idx:(npts)]))-np.sum(BGND[idx:(npts)]))+lowlim
                # print(BGND[npts-idx-1])
            if (np.abs((np.sum(BGND)-SumBGND)/SumBGND ) < err):
                break
            SumBGND = np.abs(np.sum(BGND))
    else:
        nloop=0
        while nloop < maxit:
            nloop=nloop+1
            for idx in range(npts):
                BGND[idx] = ((RangeY/(SumRTF-np.sum(BGND)))*
                    (np.sum(y[idx:npts])-np.sum(BGND[idx:npts])))+lowlim
            if (np.abs((np.sum(BGND)-SumBGND)/SumBGND ) < err):
                break
            SumBGND = np.abs(np.sum(BGND))
            
    ycorr=y-BGND
    datcorr=np.c_[x,ycorr] 

    if display:
        plt.rcParams['font.family']='Arial';plt.rcParams['font.size']= 20
        plt.rcParams['axes.linewidth']=2.5;plt.rcParams['xtick.major.width']=2.5
        plt.rcParams['xtick.labelsize']=14;plt.rcParams['figure.figsize']=(8,6)
        plt.tick_params(axis ='y', which ='both', right=False, pad=10)
        plt.tick_params(axis ='x', which ='both', top=False,pad=8)
        plt.xlabel("Binding Energy (eV)", fontsize = 30, fontname='Arial')
        plt.ylabel("Intensity (C/s)", fontsize = 30, fontname ='Arial')    
        plt.ylim(-5,(np.max(y)))
        plt.plot(x,y,'bo', label='Raw data')
        plt.plot(x,BGND, 'r:',label='BCKG', linewidth =3.0)
        plt.plot(x,ycorr,'k--',label='Subt data',linewidth=3.0)
        plt.legend(fontsize =14, loc='upper right',frameon=False)
        plt.show()
    return datcorr, BGND


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dat = pd.read_csv('O1s.csv', sep='\t')
    dat = dat.to_numpy()
    datcorr, BKG = shirley_baseline(dat,(534, 528), maxit = 50, err = 1e-6, display=True)
