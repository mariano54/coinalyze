import requests
import calendar
import time
import Gnuplot
import json
import snap
import math
import sets
import collections

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

def get_prices_json(filename):
    with open(filename, "r") as f:
        prices = json.loads(f.read())
    return prices

def get_blockchain_json(filename):
    with open(filename, 'r') as f:
        blockchain = json.loads(f.read())
    return blockchain

def add_to_network(n, block):
    # decode block
    for tx in block:
        transaction = tx.split('=')
        value = transaction[1]
        parties = transaction[0].split(':')
        outtx = int(parties[0])
        intx = int(parties[1])
        if not n.IsNode(intx):
            n.AddNode(intx)
        if not n.IsNode(outtx):
            n.AddNode(outtx)
        aux = n.AddEdge(inttx, outtx)
        n.AddIntAttrDatE(aux, value, 'value')

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
    
def network_properties(n):
    feature_set = collections.Counter()
    # Avg Clust Coeff
    feature_set['clustering coefficient'] = snap.GetClustCf(n, -1)
    # Diam
    feature_set['diameter'] = snap.GetBfsFullDiam(n, n.GetNodes()/10 if n.GetNodes() >= 10 else n.GetNodes())
    # Size Nodes
    feature_set['nodes'] = n.GetNodes()
    # Size Wcc
    feature_set['max wcc'] = snap.GetMxWcc(n).GetNodes()
    # MLE
    alphas = get_alphas(n)
    feature_set['in alpha'] = alphas[0]
    feature_set['out alpha'] = alphas[1]
    # Avg Tx value
    feature_set['avg tx value'] = sum(n.GetIntAttrE(e, 'value') for e in range(n.GetEdges()))*1.0/n.GetEdges()
    return feature_set
  
def SGD(eta, numIters, examples):

    def dotProduct(d1, d2):
        if len(d1) < len(d2):
            return dotProduct(d2, d1)
        else:
            return sum(d1.get(f, 0) * v for f, v in d2.items())

    def increment(d1, scale, d2):
        for f, v in d2.items():
            d1[f] = d1.get(f, 0) + v * scale

    def dirLoss(features, y):
        dot_product = dotProduct(weights, features)
        residual = 2 * (dot_product - y)
        new_features = collections.Counter()
        for feature in features:
            new_features[feature] = float(features[feature]) * float(residual)
        return new_features    

    weights = collections.Counter()
    for i in range(numIters):
        for entry in examples:
            y = examples[entry][-1]
            entry = examples[entry][:-1]
            increment(weights, -eta, dirLoss(entry, y))

    def classifier(example):
        return sum(weight for weight in dotProduct(weights, example))

    return classifier

def plot_prices(prices, blocks):
    xy = [(x,y) for (x,y) in sorted(prices.iteritems())][::50]   
    g = Gnuplot.Gnuplot(persist=1)
    #g('set logscale y')
    g('set pointsize 0.1')
    d1 = Gnuplot.Data(xy, with_='lp',title='Graph1') 
    #d2 = Gnuplot.Data(blocks, with_='lp',title='Graph1') 
    g.plot(d1)

def plot(M, classifier):
    xy = [x, y for x, y in sorted(M.iteritems())]
    g = Gnuplot.Gnuplot(persist=1) 
    g.('set pointsize 0.1')

    d = [Gnuplot.Data(x, y[element], with_='lp',title= element) for element in y for x, y in xy]
    for data in d:
        g.plot(data)

def writeToFile(M, filename):
    with open(filename, "a+") as f:
        for entry in M:
            f.write(entry + ':' + sorted(M[entry].iteritems())+ '\n')

def readFromFile(filename):
    M = {}
    with open(filename, 'r') as f:
        for line in f:
            contents = line.split(':')
            M[contents[0]] = collections.Counter()
            for entry in contents[1].split()

def main():
    filename = "info.out"
    N = snap.TNEANet()
    N.AddIntAttrE('value')

    M = {}
    prices = get_prices_json('prices.json')
    blockchain = get_blockchain_json('blockchain.json')
    consider_prices = True
    done = False
    if not done:
        for block in blockchain:
            if consider_prices:
                t = block[0] # adjust that price
                if t in prices:
                    add_to_network(N, block[1:])
                    M[t] = network_properties(N,)
                    M[t]['time'] = t #account for hour 
                    M[t]['price'] = prices[t] # account for hour

    numIters = 100
    eta = 0.001   
    classifier = SGD(eta, numIters, M)

    plot(M, classifier)

if __name__ == "__main__":
    main()
