import requests
import calendar
import time
import Gnuplot
import json
import snap
import math
import sets

def get_coinbase_page(page_no, prices):
    print("here")
    r = requests.get('https://api.coinbase.com/v1/prices/historical?page='+ str(page_no))
    prices_text = r.text.split('\n')
    for price_text in prices_text:      
        if ',' not in price_text or '>' in price_text:
            continue
        date = price_text.split(',')[0].split('-')[:3]
        t = time.strptime('-'.join(date)[:18], "%Y-%m-%dT%H:%M:%S")
        
        prices[calendar.timegm(t)] = price_text.split(',')[1]
    return r.status_code == 200 and r.text is not None and len(r.text) > 1

def download_prices(prices):
    while get_coinbase_page(page_no, prices):
        print(page_no)
        page_no += 1
        print(len(prices))

def store_prices(prices):
    f = open("prices.json", "w")
    f.write(json.dumps(prices))
    f.close()

def read_prices():
    f = open("prices.json", "r")
    prices = json.loads(f.read())
    f.close()
    return prices


def read_edges():
    blocks = {}
    index = 1
    blocks[index] = []
    seen_blocks = set()
    for line in open("user_edges.txt", "r"):
        ID, src, dst, time, value = [i.strip() for i in line.split(',')]
        if time not in seen_blocks:
            seen_blocks.update([time])
            if len(seen_blocks)%1000 == 0:
                index += 1
                blocks[index] = []
            if len(seen_blocks)%20000 == 0:
                return blocks
                print len(blocks)
        blocks[index].append((src, dst, value))
    
def plot_prices(prices, blocks):
    xy = [(x,y) for (x,y) in sorted(prices.iteritems())][::50]   
    g = Gnuplot.Gnuplot(persist=1)
    #g('set logscale y')
    g('set pointsize 0.1')
    d1 = Gnuplot.Data(xy, with_='lp',title='Graph1') 
    #d2 = Gnuplot.Data(blocks, with_='lp',title='Graph1') 
    g.plot(d1)



def add_to_network(n, block):
    # decode block
    for tx in block:
        if not n.IsNode(int(tx[0])):
            n.AddNode(int(tx[0]))
        if not n.IsNode(int(tx[1])):
            n.AddNode(int(tx[1]))
        n.AddEdge(int(tx[0]), int(tx[1]))

    
def get_alphas(n):
    indegpairs = snap.TIntPrV()
    outdegpairs = snap.TIntPrV()
    snap.GetInDegCnt(n, indegpairs)
    snap.GetOutDegCnt(n, outdegpairs)
    totalin = sum(pair.GetVal2() for pair in indegpairs)
    totalout = sum(pair.GetVal2() for pair in outdegpairs)
    for pair in indegpairs:
        if pair.GetVal1() == 0 or pair.GetVal1() == 1:
            a = snap.TInt(2)
            pair.Val1 = a
    for pair in outdegpairs:
        if pair.GetVal1() == 0 or pair.GetVal1() == 1:
            a = snap.TInt(2)
            pair.Val1 = a

    alphain = 1 + totalin*1.0/sum(math.log(pair.GetVal1())*pair.GetVal2() for pair in indegpairs)
    alphaout = 1 + totalout*1.0/sum(math.log(pair.GetVal1())*pair.GetVal2() for pair in outdegpairs)
    return (alphain, alphaout)
    
def compute_properties(feature_set, n):
    # Avg Clust Coeff
    feature_set.append(snap.GetClustCf(n, -1))
    # Diam
    feature_set.append(snap.GetBfsFullDiam(n, 20))
    # Size Nodes
    feature_set.append(n.GetNodes())
    # Size Wcc
    feature_set.append(snap.GetMxWcc(n).GetNodes())
    # MLE
    alphas = get_alphas(n)
    feature_set.append(alphas[0])
    feature_set.append(alphas[1])
   
  
def main():
    page_no = 1
    prices = {}

    prices = read_prices()
    blocks = read_edges()
    blocks2 = [(k, len(v)) for (k,v) in blocks.iteritems()]
    plot_prices(prices, blocks)
    quit()

    blockchain = blocks 
    outfile = "info"
    #N = snap.TNGraph(snap.PNGraph) # whatever
    N = snap.GenRndGnm(snap.PNGraph, 1, 0)
    N.DelNode(0)
    M = {}
    for block in blockchain:
        feature_set = []
        add_to_network(N, blockchain[block])
        compute_properties(feature_set, N)
        M[block] = feature_set
   
    for entry in M:
        for i in range(len(M[entry])):
            with open(outfile + '_' + str(i) + ".out", "a+") as f:
                f.write(str(entry) + '\t' + str(M[entry][i]) + '\n')
                #Fin de la conversacion
   
    #xy = [(x,y) for (x,y) in sorted(prices.iteritems())][::50]   
    #g('set logscale y')
    xy = [[(i, value[n]) for (i,(time, value)) in enumerate(sorted(M.iteritems()))] for n in range(6)]
    g = [Gnuplot.Gnuplot(persist=1) for n in range(len(xy))]
    for g1 in g:
        g1('set pointsize 0.1')

    d = [Gnuplot.Data(xy[e], with_='lp',title='Graph' + str(e)) for e in range(len(xy))]
    for (g1, d1) in zip(g, d):
        g1.plot(d1)




  

if __name__ == "__main__":
    main()
