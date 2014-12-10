import requests
import calendar
import time
import Gnuplot
import json
import snap
import math
import sets
import collections
import time
import shelve

SKIP_NUM = 1000
SKIP_NUM_CC = 10060
PRICE_INTERVAL = 1000
ALPHAS = [2.21648113774, 2.2962307812]
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
    prices = sorted([(t,v) for t,v in prices.iteritems()], key=lambda x: x[0])
    print 'loaded prices file'
    return prices

def get_blockchain_json(filename, start, end):
    blockchain = []
    f = open(filename, 'r')
    i = 0
    for line in  f:
        if i > end:
            break
	if i >= start:
            blockchain.append(json.loads(line))
    f.close()
    return blockchain


def getEdgeVal(node, g):
    try:
        val = g.GetFltAttrDatE(node, 'value')
        if val < 0:
            val = 0
        return val
    except:
        return 0

prev_avg_cc = 0
trololol = 0
added_nodes = 0
total_bitcoins = 0
max_tx_val = 0
min_tx_val = 0
total_nodes = 0
total_edges = 0
#@profile
def add_to_network(n, block, nodeids):
    old_num_nodes = n.GetNodes()
    prev_neighbors_cc = 0
    new_neighbors_cc = 0
    new_nodes_cc = 0
    new_edges = []
    new_nodes = set()
    neighbors = set()
    ccfs = collections.Counter()
    global prev_avg_cc
    global added_nodes
    global total_bitcoins
    global max_tx_val
    global min_tx_val
    global total_nodes
    global total_edges
    max_tx_val = -float('inf')
    min_tx_val = float('inf')
    added_nodes = 0
    for tx in block:
        transaction = tx.split('=')
        value = int(transaction[1])/100000000
        total_bitcoins += value 
        if value > max_tx_val:
            max_tx_val = value
        if value < min_tx_val:
            min_tx_val = value
        parties = transaction[0].split(':')
        outtx = parties[0].encode("utf-8")
        intx = parties[1].encode("utf-8")
        if intx not in nodeids:
            nodeids[intx] = total_nodes
            total_nodes += 1
            added_nodes += 1
        if outtx not in nodeids:
            nodeids[outtx] = total_nodes
            total_nodes += 1
            added_nodes += 1
        total_edges += 1
        #if not n.IsEdge(nodeids[intx], nodeids[outtx]):
           # n.AddEdge(nodeids[intx], nodeids[outtx])

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

    alphain = 1 + totalin*1.0/(1+sum(math.log(pair.GetVal1())*pair.GetVal2() for pair in indegpairs))
    alphaout = 1 + totalout*1.0/(1+ sum(math.log(pair.GetVal1())*pair.GetVal2() for pair in outdegpairs))
    return (alphain, alphaout)

prev_clust_coeff = 0
prev_num_trans = 0
prev_avg_trans_val = 0
prev_total_trans_val = 0
def get_avg_tx(block, num_nodes, num_edges):
    global prev_num_trans
    global prev_avg_trans_val
    global prev_total_trans_val
    new_total_trans_val = sum([int(t.split("=")[1]) for t in block]) / (100000000.0)
    prev_avg_trans_val = ((prev_num_trans * prev_avg_trans_val) + new_total_trans_val) / \
            float(prev_num_trans + len(block))
    prev_num_trans += len(block)
    prev_total_trans_val += new_total_trans_val

prev_alphas = [0,0]
prev_max_wcc = 0
smooth_block_size = []
smooth_min_tx_val = []
smooth_max_tx_val = []
def network_properties(n, block, feature_set, block_num):
    num_nodes = total_nodes
    num_edges = total_edges
    # Added nodes
    #-------------------
    feature_set['added nodes'] = added_nodes
    # Avg balance
    #------------------
    feature_set['avg balance'] = total_bitcoins/float(num_nodes)
    # Avg Clust Coeff: no
    #------------------
    #if prev_avg_cc == 0 or block_num % SKIP_NUM_CC == 2:
    #    global prev_avg_cc
    #    feature_set['avg clust cf'] = snap.GetClustCf(n)
    #    prev_avg_cc = feature_set['avg clust cf']
    #else:
    #    feature_set['avg clust cf'] = prev_avg_cc
    # Avg k: yes
    #--------------------
    feature_set['avg k'] = num_edges / (2.0*num_nodes)
    # Avg Tx value: yes
    #--------------------
    get_avg_tx(block, num_nodes, num_edges)
    feature_set['avg tx value'] = prev_avg_trans_val
    # Block size
    #-------------------
    feature_set['block size'] = len(block)
    # Block size smooth
    #-------------------
    if len(smooth_block_size) == 100:
        del smooth_block_size[0]
    smooth_block_size.append(len(block))
    feature_set['block size smooth'] = sum(smooth_block_size)/float(len(smooth_block_size))
    # Diam: no
    #-------------------
    #feature_set['diameter'] = snap.GetBfsFullDiam(n, n.GetNodes()/10 if n.GetNodes() >= 10 else n.GetNodes())
    # Size Edges: yes
    #--------------------
    feature_set['edges'] = num_edges
    # Size Nodes: yes
    #-------------------
    feature_set['nodes'] = num_nodes
    # Max Tx Val smooth
    #-------------------
    if len(smooth_max_tx_val) == 100:
        del smooth_max_tx_val[0]
    smooth_max_tx_val.append(max_tx_val)
    feature_set['max tx val smooth'] = sum(smooth_max_tx_val)/float(len(smooth_max_tx_val))
    # Min Tx Val smooth
    #--------------------
    if len(smooth_min_tx_val) == 100:
        del smooth_min_tx_val[0]
    smooth_min_tx_val.append(min_tx_val)
    feature_set['min tx val smooth'] = sum(smooth_min_tx_val)/float(len(smooth_min_tx_val))
    # MLE: n/a
    #--------------------
    if prev_alphas == [0,0] or block_num % SKIP_NUM == 0:
        alphas = ALPHAS #get_alphas(n)
        feature_set['mle in alpha'] = alphas[0]
        feature_set['mle out alpha'] = alphas[1]
        prev_alphas[0] = alphas[0]
        prev_alphas[1] = alphas[1]
    else:
       feature_set['mle in alpha'] = prev_alphas[0]
       feature_set['mle out alpha'] = prev_alphas[1]
    
  
def SGD(eta, numIters, infile, outfile):
    print 'intializing sgd'
    def dotProduct(d1, d2):
        if len(d1) < len(d2):
            return dotProduct(d2, d1)
        else:
	    return sum(d1[f] * d2[f] for f in d2)

    def increment(d1, scale, d2):
        for f, v in d2.items():
            d1[f] = d1.get(f, 0) + v * scale

    def dirLoss(weights, features, y):
        dot_product = dotProduct(weights, features)
        residual = 2 * (dot_product - y)
        new_features = collections.Counter()
        for feature in features:
            new_features[feature] = float(features[feature]) * float(residual)
        return new_features    

    weights = collections.Counter()
    for i in range(numIters):
	print 'learner iteration #', i
        with open(infile, 'r') as example_set:
	    j = 0
            for example in example_set:
		j += 1
  		if j == 10:
		    break
		if example[0] == '#':
		    continue
		example = example.split('\t')
                y = float(example[1])
                entry = collections.Counter()
                for i,e in enumerate(example):
		    if i > 1 and not e == '\n':
			entry[str(i)] = float(e)	
		grad = dirLoss(weights, entry, y)
		increment(weights, -eta, grad)
		print '\t', weights
	print weights
    with open(outfile, 'w+') as weights_file:
	weights_file.write(json.dumps(dict(weights)))

    def classifier(example):
        return sum(weight for weight in dotProduct(weights, example))

    return classifier
def fill(s):
    while len(s) < 15:
        s += " "
    return s

def toString(entry, out):
    for e in sorted(entry.iteritems(), key=lambda x: x[0]):
        out.write(fill(str(e[1])) + '\t')
    out.write('\n')

def IntroString(entry, out):
    out.write('#')
    for e in sorted(entry.iteritems(), key=lambda x: x[0]):
        out.write(fill(str(e[0]))+ '\t')
    out.write('\n')

def status(item, blockn, mem, nt):
    return 'block #' + str(blockn) + ' entry:' + str(item) + ' mem_status:' + str(mem) + ' num_trans:' + str(nt -1)

def plot(M, classifier):
    """
    xy = [(x,y) for x, y in sorted(M.iteritems())]
    g = Gnuplot.Gnuplot(persist=1) 
    g('set pointsize 0.1')

    d = [Gnuplot.Data(x, y[element], with_='lp',title= element) for element in y for x, y in xy]
    for data in d:
        g.plot(data)
   """

#@profile
def main():
    properties_name = 'properties.out'
    blockchain_name = 'blocks_full.json'
    weights_name = 'weights.json'
    prices_name = 'prices.json'
    plot_name = 'plot.out'
    N = snap.PNEANet.New()

    M = {}
    prices = get_prices_json(prices_name)
    price_index = 0;
    done = False
    nIters = 104000
    #nodeids = shelve.open("node_ids")
    nodeids = {}
    properties = collections.Counter()
    printed = 0
    if not done:
	with open(blockchain_name, 'r') as blockchain:
	    with open(properties_name, 'w') as out:
                counter = 0
                printedIntro = False
                for line in blockchain:
                    counter += 1
                    #if counter < 100000:
                    #    continue

                    block = json.loads(line)
                    if len(block) == 1:
                        continue
     	            if price_index > nIters:
	                break
                    print status(price_index, counter, len(nodeids), len(block))
                    add_to_network(N, block[1:], nodeids)
                    t = int(block[0])/1000
                    if t < int(prices[0][0]):
                        continue
                    while t > int(prices[price_index][0]):
                        price_index += 1
                    network_properties(N, block[1:], properties, counter)
                    properties['time'] = int(t) 
                    properties['price'] = float(prices[price_index][1])
                    printed += 1
                    #if printed > 113863:
                    #if printedIntro == False:
                    #    printedIntro = True
                    #    IntroString(properties, out)
                    toString(properties, out)
                    properties.clear()

    eta = 0.00000000001
    classifier_iters = 100
    #classifier = SGD(eta, classifier_iters, properties_name, weights_name)
    # TODO: test classifier
    # TODO: plot from file

if __name__ == "__main__":
    main()
