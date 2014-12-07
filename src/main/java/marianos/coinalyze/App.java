package marianos.coinalyze;
import com.google.bitcoin.core.Block;
import com.google.bitcoin.core.NetworkParameters;
import com.google.bitcoin.core.PrunedException;
import com.google.bitcoin.core.Transaction;
import com.google.bitcoin.params.MainNetParams;
import com.google.bitcoin.store.BlockStoreException;
import com.google.bitcoin.utils.BlockFileLoader;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.ArrayList;  
import java.util.HashMap;
import java.util.List;
import java.util.Map;


/**
 * Hello world!
 *
 */
public class App 
{
    public static void main( String[] args )
    {
        System.out.println( "Hello World!" );
     // Arm the blockchain file loader.
        NetworkParameters np = new MainNetParams();
        List<File> blockChainFiles = new ArrayList<File>();
        blockChainFiles.add(new File("/home/marianos/Downloads/Torrents/bootstrap.dat"));
        BlockFileLoader bfl = new BlockFileLoader(np, blockChainFiles);

        // Data structures to keep the statistics.
        Map<String, Integer> monthlyTxCount = new HashMap<String, Integer>();
        Map<String, Integer> monthlyBlockCount = new HashMap<String, Integer>();

        // Iterate over the blocks in the dataset.
    	System.out.println("@");

        for (Block block : bfl) {
        	//System.out.println("5");
        	String month = new SimpleDateFormat("yyyy-MM").format(block.getTime());
        	System.out.println(month);
        }
    }
}
