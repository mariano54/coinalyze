import requests
import calendar
import time
import Gnuplot
import json
import snap
import math
import sets
import collections

SKIP_NUM = 144

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


prev_avg_cc = 0
added_nodes = 0
#@profile
def add_to_network(n, block, nodeids):
    old_num_nodes = n.GetNodes()
    prev_neighbors_cc = 0
    new_neighbors_cc = 0
    num_neighbors = 0
    num_new_nodes = 0
    new_nodes_cc = 0
    for tx in block:
        transaction = tx.split('=')
        value = int(transaction[1])/100000000
        parties = transaction[0].split(':')
        outtx = parties[0]
        intx = parties[1]

        e_id = 0
        if intx not in nodeids and outtx not in nodeids:
            new_nodes_cc += 1
            num_new_nodes += 2
            nodeids[intx] = n.AddNode()
            nodeids[outtx] = n.AddNode()
            e_id = n.AddEdge(nodeids[intx], nodeids[outtx])
        else:
            if intx in nodeids and outtx in nodeids:
                a_neighbors = snap.TIntV()
                b_neighbors = snap.TIntV()
                snap.GetNodesAtHop(n, nodeids[intx], a_neighbors, 1, False)
                snap.GetNodesAtHop(n, nodeids[outtx], b_neights, 1, False)
                neighbors = set(nodeids[intx], nodeids[outtx])
                neighbors.update(a_neighbors)
                neighbors.update(b_neighbors)
                for neighbor in neighbors:
                    prev_neighbors_cc += snap.GetNodeClustCf(n, neighbor)
                e_id = n.AddEdge(nodeids[intx], nodeids[outtx])
                for neighbor in neighbors:
                    new_neighbors_cc += snap.GetNodeClustCf(n, neighbor)
            if outtx in nodeids:
                prev_neighbors_cc += snap.GetNodeClustCf(n, nodeids[outtx])
                nodeids[intx] = n.AddNode()
                e_id = n.AddEdge(nodeids[intx], nodeids[outtx])
                new_neighbors_cc += snap.GetNodeClustCf(n, nodeids[outtx])
                new_nodes_cc += snap.GetNodeClustCf(n, nodeids[intx])
                num_new_nodes += 1
            if intx in nodeids:
                prev_neighbors_cc += snap.GetNodeClustCf(n, nodeids[intx])
                nodeids[outtx] = n.AddNode()
                e_id = n.AddEdge(intx, outtx)
                new_neighbors_cc += snap.GetNodeClustCf(n, nodeids[intx])
                new_nodes_cc += snap.GetNodeClustCf(n, nodeids[outtx])
                num_new_nodes += 1

        new_val = value + n.GetFltAttrDatE(e_id, 'value')
        n.AddFltAttrDatE(e_id, new_val, 'value')

    added_nodes = num_new_nodes
    prev_avg_cc = (prev_avg_cc*old_num_nodes - prev_neighbors_cc + new_neighbors_cc + num_new_nodes*new_nodes_cc)/float(n.GetNodes())

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

def network_properties(n, block, feature_set, block_num):
    num_nodes = n.GetNodes()
    num_edges = n.GetEdges()
    # Added nodes
    #-------------------
    feature_set['added nodes'] = added_nodes
    # Avg Clust Coeff: no
    #-------------------
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
    
    global prev_max_wcc
    # Size Wcc: n/a
    #--------------------
    if prev_max_wcc == 0 or block_num % SKIP_NUM == 1:
        feature_set['wcc'] = snap.GetMxWcc(n).GetNodes()
        prev_max_wcc = feature_set['wcc']
    else:
        feature_set['wcc'] = prev_max_wcc
  
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
    return '\t'.join([str(e[1]) for e in sorted(entry.iteritems(), key=lambda x: x[0])])

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
    nIters = 200000
    nodeids = {}
    properties = collections.Counter()
    if not done:
	with open(blockchain_name, 'r') as blockchain:
	    with open(properties_name, 'w') as out:
                counter = 0
                for line in blockchain:
		    counter += 1
		    block = json.loads(line)
                    if len(block) == 1:
                        continue
     		    if price_index > nIters:
	                break
		    add_to_network(N, block[1:], nodeids)
		    t = int(block[0])/1000
		    if t < int(prices[0][0]):
                continue
		    print status(price_index, counter, len(nodeids), len(block))
            while t > int(prices[price_index][0]):
                price_index += 1
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
