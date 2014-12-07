package marianos.coinalyze;
import com.google.bitcoin.core.Address;
import com.google.bitcoin.core.Block;
import com.google.bitcoin.core.NetworkParameters;
import com.google.bitcoin.core.PrunedException;
import com.google.bitcoin.core.Transaction;
import com.google.bitcoin.core.TransactionInput;
import com.google.bitcoin.core.TransactionOutput;
import com.google.bitcoin.params.MainNetParams;
import com.google.bitcoin.script.Script;
import com.google.bitcoin.store.BlockStoreException;
import com.google.bitcoin.utils.BlockFileLoader;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.UnsupportedEncodingException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;  
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.json.simple.JSONObject;
import org.json.simple.JSONArray;
import org.json.simple.parser.ParseException;
import org.json.simple.parser.JSONParser;



/**
 * Hello world!
 *
 */
public class App 
{

	public static void main( String[] args ) throws IOException
	{
		System.out.println( "Hello World!" );
		// Arm the blockchain file loader.
		NetworkParameters np = new MainNetParams();
		List<File> blockChainFiles = new ArrayList<File>();
		blockChainFiles.add(new File("/home/marianos/Downloads/Torrents/bootstrap.dat"));
		BlockFileLoader bfl = new BlockFileLoader(np, blockChainFiles);

		
		// Iterate over the blocks in the dataset.
		System.out.println("@");

        FileWriter file = new FileWriter("blocks.json");
        try {
            file.write("[");
            System.out.println("Started writing...");
 //           System.out.println("\nJSON Object: " + obj);
 
        } catch (IOException e) {
            e.printStackTrace();
            file.flush();
            file.close();
        } 

		for (Block block : bfl) {
			JSONArray block_json = new JSONArray();
			block_json.add(block.getTime().toString());
			//System.out.println("5");
			for (Transaction t : block.getTransactions()){
				//	System.out.println(t);
				String[] T = new String[3];
				T[0] = "0";
				for (TransactionInput ti : t.getInputs()){
					for (TransactionOutput to : t.getOutputs()){
						Script s = to.getScriptPubKey();
						if (s.isSentToAddress()){
							String input_addr = "0";
							//T[0] = Integer.parseInt(T[0]) + ti.
							try{
								if (!ti.isCoinBase()){
									String from_addr =  ti.getFromAddress().toString();
									String to_addr =  s.getToAddress(np).toString();
									String value = to.getValue().toString();
									//System.out.print("F: " + from_addr + " to " + to_addr + ": " + value);
									String write_str = to_addr + ":" + from_addr + "=" + value; 
									block_json.add(write_str);
								}
							}catch(Exception e){
								//System.out.println("no input addr");
							}
							//System.out.print("Output addr: ");
							//System.out.println(s.getToAddress(np));
						}
					}
				}
			}
			

	        try {
	            file.write(block_json.toJSONString() + ", ");
	            //System.out.println("Successfully Copied JSON Object to File...");
	 //           System.out.println("\nJSON Object: " + obj);
	 
	        } catch (IOException e) {
	            e.printStackTrace();
	            file.flush();
	            file.close();
	        } 
			System.out.println(block.getTime());
		}
        try {
            file.write("]");
            System.out.println("Successfully Copied JSON Object to File...");
 //           System.out.println("\nJSON Object: " + obj);
 
        } catch (IOException e) {
            e.printStackTrace();
            file.flush();
            file.close();
        } 
		 file.flush();
         file.close();
		
	}
}	

