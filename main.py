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

SKIP_NUM = 216
SKIP_NUM_CC = 5160
PRICE_INTERVAL = 1000

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
added_nodes = 0
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
    for tx in block:
        transaction = tx.split('=')
        value = int(transaction[1])/100000000
        parties = transaction[0].split(':')
        outtx = parties[0].encode("utf-8")
        intx = parties[1].encode("utf-8")
        """
        if intx not in nodeids and outtx not in nodeids:
            print 'nobody in'
            nodeids[intx] = n.AddNode()
            nodeids[outtx] = n.AddNode()
            new_nodes.update([nodeids[intx], nodeids[outtx]])
            new_edges.append((nodeids[intx], nodeids[outtx]))
        else:
            if intx in nodeids and outtx in nodeids:
                print 'both in'
                start = time.time()
                a_neighbors = snap.TIntV()
                b_neighbors = snap.TIntV()
                snap.GetNodesAtHop(n, nodeids[intx], 1, a_neighbors, False)
                snap.GetNodesAtHop(n, nodeids[outtx], 1, b_neighbors, False)
                neighbors.update([nodeids[intx], nodeids[outtx]])
                neighbors.update(a_neighbors)
                neighbors.update(b_neighbors)
                new_edges.append((nodeids[intx], nodeids[outtx]))
                print 'took', time.time() - start
            if outtx in nodeids:
                print 'out in'
                start = time.time()
                nodeids[intx] = n.AddNode()
                new_nodes.update([nodeids[intx]])
                neighbors.update([nodeids[outtx]])
                new_edges.append((nodeids[intx], nodeids[outtx]))
                print 'took', time.time() - start
            if intx in nodeids:
                print 'in in'
                start = time.time()
                nodeids[outtx] = n.AddNode()
                new_nodes.update([nodeids[outtx]])
                neighbors.update([nodeids[intx]])
                new_edges.append((nodeids[intx], nodeids[outtx]))
                print 'took', time.time() - start
        print 'iterations'
        start = time.time()
        print len(neighbors)
        print len(neighbors)
        for neighbor in neighbors:
            v = snap.TIntV()
            snap.GetNodesAtHop(n, neighbor, 1 ,v, False)
            print 'neighbors or neighbor', len(v)
            prev_neighbors_cc += snap.GetNodeClustCf(n, neighbor)
            pass
        print 'took1', time.time() - start

        for to, fro in new_edges:
            ID = n.AddEdge(to, fro)
            n.AddFltAttrDatE(ID, getEdgeVal(ID, n) + value, 'value')
            pass
        print 'took2', time.time() - start
        
        for neighbor in neighbors:
            new_neighbors_cc += snap.GetNodeClustCf(n, neighbor)
            pass

        print 'took3', time.time() - start
        #new_nodes_cc = sum(snap.GetNodeClustCf(n, node) for node in new_nodes)
        """
        if intx not in nodeids:
            nodeids[intx] = n.AddNode()
        if outtx not in nodeids:
            nodeids[outtx] = n.AddNode()
        ccfs[nodeids[intx]] = snap.GetNodeClustCf(n, nodeids[intx])
        ccfs[nodeids[outtx]] = snap.GetNodeClustCf(n, nodeids[outtx])
        new_nodes.update([nodeids[intx], nodeids[outtx]])
        eid = n.AddEdge(nodeids[intx], nodeids[outtx])
        n.AddFltAttrDatE(eid, getEdgeVal(eid, n) + value, 'value')
        n.AddFltAttrDatE(eid, str(nodeids[intx]) + ':' + str(nodeids[outtx]), 'dir')
    
    for node in new_nodes:
        ccfs[node] = snap.GetNodeClustCf(n, node)
    prev_avg_cc = sum(ccfs[i] for i in ccfs)/float(len(ccfs))
    #added_nodes = len(new_nodes)
    #prev_avg_cc = snap.GetClustCf(n)#(prev_avg_cc*old_num_nodes - prev_neighbors_cc + new_neighbors_cc + len(new_nodes)*new_nodes_cc)/float(n.GetNodes())
    #print 'cc', prev_avg_cc

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
    prev_avg_trans_val = ((prev_num_trans * prev_avg_trans_val) + new_total_trans_val) / float(prev_num_trans + len(block))
    prev_num_trans += len(block)
    prev_total_trans_val += new_total_trans_val

prev_alphas = [0,0]
prev_max_wcc = 0

def get_avg_addr_balance(block):
    seen = {}
    for transaction in block:
        if transaction not in seen:
            v = snap.TIntV()
            snap.GetNodesAtHop(n, neighbor, 1 ,v, False)
            for neighbor in v:
                pass

    

def network_properties(n, block, feature_set, block_num):
    num_nodes = n.GetNodes()
    num_edges = n.GetEdges()
    # Added nodes
    #-------------------
    feature_set['added nodes'] = added_nodes
    # Avg Clust Coeff: no
    #------------------
    #if prev_avg_cc == 0 or block_num % SKIP_NUM_CC == 2:
    #    global prev_avg_cc
    #    feature_set['avg clust cf'] = snap.GetClustCf(n)
    #    prev_avg_cc = feature_set['avg clust cf']
    #else:
    feature_set['avg clust cf'] = prev_avg_cc
    # Avg k: yes
    #--------------------
    feature_set['avg k'] = num_edges / (2.0*num_nodes)
    # Avg Tx value: yes
    #--------------------
    get_avg_tx(block, num_nodes, num_edges)
    feature_set['avg tx value'] = prev_avg_trans_val
    # Diam: no
    #-------------------
    #feature_set['diameter'] = snap.GetBfsFullDiam(n, n.GetNodes()/10 if n.GetNodes() >= 10 else n.GetNodes())
    # Size Edges: yes
    #--------------------
    feature_set['edges'] = num_edges
    # Size Nodes: yes
    #-------------------
    feature_set['nodes'] = num_nodes
    # MLE: n/a
    #--------------------
    if prev_alphas == [0,0] or block_num % SKIP_NUM == 0:
        alphas = get_alphas(n)
        feature_set['mle in alpha'] = alphas[0]
        feature_set['mle out alpha'] = alphas[1]
        prev_alphas[0] = alphas[0]
        prev_alphas[1] = alphas[1]
    else:
       feature_set['mle in alpha'] = prev_alphas[0]
       feature_set['mle out alpha'] = prev_alphas[1]
    
    #global prev_max_wcc
    # Size Wcc: n/a
    #--------------------
    #if prev_max_wcc == 0 or block_num % SKIP_NUM == 1:
    #    feature_set['wcc'] = snap.GetMxWcc(n).GetNodes()
    #    prev_max_wcc = feature_set['wcc']
    #else:
    #    feature_set['wcc'] = prev_max_wcc
  
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

def toString(entry):
    result = ''
    for e in sorted(entry.iteritems(), key=lambda x: x[0]):
        result += str(e[1]) + '\t'
    return result

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
    if not done:
	with open(blockchain_name, 'r') as blockchain:
	    with open(properties_name, 'w') as out:
                counter = 0
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
                    if len(prices) % (price_index + 1) == PRICE_INTERVAL: 
                        network_properties(N, block[1:], properties, counter)
                        properties['time'] = int(t) 
                        properties['price'] = float(prices[price_index][1])
                        out.write(str(prices[price_index][0]) + '\t' + toString(properties) + '\n')
                        properties.clear()

    eta = 0.00000000001
    classifier_iters = 100
    #classifier = SGD(eta, classifier_iters, properties_name, weights_name)
    # TODO: test classifier
    # TODO: plot from file

if __name__ == "__main__":
    main()
