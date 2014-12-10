import Gnuplot
import time
import datetime
from scipy.stats.stats import pearsonr
SKIP_NUM = 2

def scale(xy, max_price):
    max_y = max([pr[1] for pr in xy])
    ratio = max_price/max_y
    
    return [(x, y*ratio) for x,y in xy]

def getTime(date_str, init):
    date = datetime.date.fromtimestamp(date_str)
    return init * 100 + date.month

def plotvsprice(g, ds, titles, xys, item, logscale=False, save=False, savename = 'output.png'):
    if logscale:
        g('set logscale y')

    g.plot(ds[titles.index(item)], ds[titles.index('price')])
    
    if save:
        g.hardcopy(savename,terminal = 'png')

    print pearsonr([y for x, y in xys[titles.index('price')]], [y for x, y in xys[titles.index(item)]]) 

def main():
    properties = []
    titles = []
    with open('properties_alphas.out', 'r') as f:
        for line in f:
            titles = [l.strip().strip("#") for l in line.split("\t")[:-1]]
            break

    with open("properties.out") as props:
        i = 0
        for line in props:
            i += 1
            if i % SKIP_NUM != 0: continue
            properties.append([float(p.strip()) for p in line.split("\t")[:-1]]) 

    xys = []
    for prop_index in xrange(len(properties[0])):
        xys.append([(getTime(bl[-1], i), bl[prop_index]) for i, bl in enumerate(properties)])

    g = Gnuplot.Gnuplot(persist=1)
    ds = []
    ds_alpha_price = None
    max_price = max([pr[1] for pr in xys[titles.index("price")]])
    if False:
        for i, gr in enumerate(xys):
            ds.append(Gnuplot.Data(gr, with_='lp',title=titles[i]))
        gr = scale(xys[titles.index("price")], 2.5)
        ds_alpha_price = Gnuplot.Data(gr, with_='lp',title="price")
    else:
        for i, gr in enumerate(xys):
            gr = scale(gr, max_price)
            ds.append(Gnuplot.Data(gr, with_='lp',title=titles[i]))

    ds0 = Gnuplot.Data(xys[0], with_='lp',title=titles[0])

    
    # Alphas analysis
#=====================================
    #g.plot(ds[titles.index("mle out alpha")], ds[titles.index("mle in alpha")])
    #g.hardcopy('alphas_analysis.png',terminal = 'png')
    
    # Added Nodes Log
#=====================================
    #g('set logscale y')
    #g.plot(ds[0], ds[titles.index('price')])
    #g.hardcopy('added_nodes_vs_price_log.png',terminal = 'png')
    #print pearsonr([y for x, y in xys[titles.index('price')]], [y for x, y in xys[titles.index('added nodes')]]) 
    
    # Added Nodes Regular
#=====================================
    #g.plot(ds[0], ds[titles.index('price')])
    #g.hardcopy('added_nodes_vs_price_reg.png',terminal = 'png')
    #print pearsonr([y for x, y in xys[titles.index('price')]], [y for x, y in xys[titles.index('added nodes')]])     
    
    # Avg balance
#======================================
    #g.plot(ds[1], ds[titles.index('price')])
    #print pearsonr([y for x, y in xys[titles.index('price')]], [y for x, y in xys[1]]) 

    # Edges
#======================================
    #plotvsprice(g, ds, titles, xys, 'edges', logscale = True, save=True, savename='edges_vs_price_log.png')   

#Avg Tx value
#======================================
    #plotvsprice(g, ds, titles, xys, 'avg tx value', save=True, savename='avg_tx_val_vs_price.png')   
    #plotvsprice(g, ds, titles, xys, 'avg tx value', logscale=True, save=True, savename='avg_tx_val_vs_price_log.png')   
#Block Size, BlockSize Smooth
#=======================================
    #plotvsprice(g, ds, titles, xys, 'block size', save=True, savename='block_size_vs_price.png')
    #time.sleep(5)
    #plotvsprice(g, ds, titles, xys, 'block size smooth', save=True, savename='block_size_smooth_vs_price.png')
    #plotvsprice(g, ds, titles, xys, 'block size smooth', logscale=True)

# Mx tx val
#======================================
    #plotvsprice(g, ds, titles, xys, 'max tx val smooth', logscale=True)

# Avg k (deg)
#=====================================
    #plotvsprice(g, ds, titles, xys, 'avg k', save=True, savename='avg_k_vs_price.png')
    #print titles

#Nodes
#=====================================
    plotvsprice(g, ds, titles, xys, 'nodes')
if __name__ == "__main__":
    main()
