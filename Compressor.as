package {

	import flash.display.Sprite;
	import flash.events.Event;
	import flash.net.FileFilter;
	import flash.net.FileReference;
	import flash.text.TextField;
	import flash.utils.*;

	/**
	 * ...
	 * @author Ace 
	 * Modify by Jimbowhy
	 * 
	 * http://stackoverflow.com/questions/12121062/how-to-decompress-a-lzma-compressed-file-using-bytearray-method-in-as3
	 * This is the code that I'am using to compress/decompress files.
	 * 
	 * My problem : This method doesn't decompress LZMA compressed files :(
	 * Can anyone please tell me how to restructure the above code to achieve LZMA decompression
	 * and whether the above compression code is good enough for LZMA-compression?If not, 
	 * please do give an example of it.
	 * 
	 * EDIT : After long hours of searching,I got this but I can't quite understand the 
	 * example code in it :( Some help,anyone?
	 * https://helpx.adobe.com/flash-player/kb/exception-thrown-you-decompress-lzma-compressed.html
	 */

	public class Compressor extends Sprite
	{
		private var ref:FileReference;
		private var txf:TextField;
		private var buffer:ByteArray;
		private var glue:String = "";
		private var dos:String = "Nothing";
		private var MAGIC_ZWS:String = "ZWS";
		private var MAGIC_CWS:String = "CWS";
		private var MAGIC_FWS:String = "FWS";
		private var MAGIC_EBT:String = "YBD";
		private var MAGIC_EBK:String = "EBT_PK";
		private var MAKEUP:Boolean = true;

		public function Compressor()
		{
			txf = new TextField();
			txf.text = "SWF Compressor and Decompressor";
			txf.width = txf.textWidth + 200;
			txf.x = stage.stageWidth / 2 - txf.width / 2;
			txf.y = stage.stageHeight / 2 - txf.height / 2;
			parent.addChild(txf);
			open();
		}
		
		private function open():void
		{
			ref = new FileReference();
			ref.addEventListener(Event.SELECT, load);
			ref.browse([new FileFilter("SWF Files", "*.swf;*.ebt")]);			
		}
		
		private function load(e:Event):void
		{
			ref.addEventListener(Event.COMPLETE, processSWF);
			ref.load();
		}

		private function processSWF(e:Event):void
		{
			var swf:ByteArray;
			dos = ref.data.readMultiByte(3, "us-ascii");
			switch(dos)
			{
				case MAGIC_CWS:
					swf = decompress(ref.data);
					break;
				case MAGIC_ZWS:
					txf.text = "ZWS detected, donothing. SWF 13 and later use LZMA.";
					break;
				case MAGIC_FWS:
					swf = compress(ref.data);
					break;
				case MAGIC_EBT:
					swf = decompressEBT_PH(ref.data);
					break;
				default:
					//throw Error("Not SWF...");
					dos = MAGIC_EBK;
					swf = decompressEBT_PK(ref.data); // ebt is a compress file and light encrypt
					break;
			}
			if ( swf && glue && MAKEUP) {
				txf.text = "Need the 2nd part of ebt to makeup a page.";
				open(); // deal the 2nd part of ebt.
				MAKEUP = false
			}else if (swf && glue && dos!=glue) {
				var b:Boolean = glue == MAGIC_EBT;
				swf = makeup(b?buffer:swf, b?swf:buffer);
				glue = null;
			}
			
			if( (swf && !glue) || dos==glue ){
				txf.text = dos + " Dectected.";
				new FileReference().save(swf);
			}
		}
		
		private function makeup(ebt_ph:ByteArray, ebt_pk:ByteArray):ByteArray
		{
			var buff:ByteArray = new ByteArray();
			ebt_ph.position = 0;
			ebt_pk.position = 0;
			buff.endian = Endian.LITTLE_ENDIAN;
			buff.writeBytes(ebt_ph, 0, ebt_ph.bytesAvailable);
			buff.writeBytes(ebt_pk, 0, ebt_pk.bytesAvailable);
            buff.writeByte(64); // make 4 bytes ending
            buff.writeByte(0);
            buff.writeByte(0);
            buff.writeByte(0);
            buff.position = 4;
            buff.writeUnsignedInt(buff.length); // write file size back to header
            buff.position = 0;
			return buff;
		}
		
		private function decompressEBT_PH(data:ByteArray):ByteArray
		{
			data.position = 40; // 40 bytes bypass
			var buff:ByteArray = new ByteArray();
			buff.endian = Endian.LITTLE_ENDIAN;
			var ebt:ByteArray = new ByteArray();
			ebt.endian = Endian.LITTLE_ENDIAN;
			//ebt.writeBytes(data, 0, data.bytesAvailable); // different below
			data.readBytes(ebt, 0, data.bytesAvailable);
			try {
				ebt.uncompress();
				buff.writeBytes(ebt, 0, ebt.length);
				buff.position = 4;
				buff.writeUnsignedInt(buff.length);
			}catch (e:Error) {
				txf.text = e.message + " at line:" + /\\.+\.as:([0-9]+)]/.exec(e.getStackTrace())[1];
				return null;
			}
			if (!buffer) {
				buffer = buff;
				glue = MAGIC_EBT;
			}
			return buff;
		}
		private function decompressEBT_PK(data:ByteArray):ByteArray
		{
			data.position = 32; // 32bytes bypass in pk ebt
			var ebt:ByteArray = new ByteArray();
			var buff:ByteArray = new ByteArray();
			ebt.endian = Endian.LITTLE_ENDIAN;
			buff.endian = Endian.LITTLE_ENDIAN;
			data.readBytes(buff, 0, data.bytesAvailable);
			try {
				buff.uncompress();
				ebt.writeMultiByte(MAGIC_FWS, "ANSI");
				//ebt.position = 4;
				//ebt.writeUnsignedInt(buff.length+8);
				ebt.writeBytes(buff);
			} catch (e:Error) {
				txf.text = e.message + " at line:" + /\\.+\.as:([0-9]+)]/.exec(e.getStackTrace())[1];
				return null;
			}
			if (!buffer) {
				buffer = buff;
				glue = MAGIC_EBK;
			}
			return ebt;
		}
		
		private function compress(data:ByteArray):ByteArray
		{
			var header:ByteArray = new ByteArray();
			var decompressed:ByteArray = new ByteArray();
			var compressed:ByteArray = new ByteArray();

			header.writeBytes(data, 3, 5); //read the header, excluding the signature
			decompressed.writeBytes(data, 8); //read the rest

			decompressed.compress();

			compressed.writeMultiByte("CWS", "us-ascii"); //mark as compressed
			compressed.writeBytes(header);
			compressed.writeBytes(decompressed);

			return compressed;
		}

		private function decompress(data:ByteArray):ByteArray
		{
			var header:ByteArray = new ByteArray();
			var compressed:ByteArray = new ByteArray();
			var decompressed:ByteArray = new ByteArray();

			header.writeBytes(data, 3, 5); //read the uncompressed header, excluding the signature
			compressed.writeBytes(data, 8); //read the rest, compressed

			compressed.uncompress();

			decompressed.writeMultiByte("FWS", "us-ascii"); //mark as uncompressed
			decompressed.writeBytes(header); //write the header back
			decompressed.writeBytes(compressed); //write the now uncompressed content

			return decompressed;
		}

		
	}
}