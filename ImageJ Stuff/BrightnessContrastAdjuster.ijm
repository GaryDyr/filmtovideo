
//must open a avi file using PSI_avi_Procesor v2.py
//and run it to a particular slice
//Place slice title in next line
selectWindow("slice_4");
run("Duplicate...", "title=slice_4-1");
//run("Brightness/Contrast...");
abase = 160;
amin = 0;
amax = 212;
for (n=0; n<10;n++) {
	//amin = abase - n*5;
	//amax = abase + n*5;
	//amin = amin - n;
	amax = amax + n*2;
	selectWindow("template");
	run("Duplicate...", "title=template-1");
	setMinAndMax(amin, amax);
	//run("Apply LUT");
	run("Calculator Plus", "i1=slice_4-1 i2=template-1 operation=[Add: i2 = (i1+i2) x k1 + k2] k1=1 k2=0 create");
	selectWindow("template-1");
	close;
	selectWindow("Result");
	rstr = "R:" + d2s(amin,0) + "-" + d2s(amax,0);
	//aTitle = getTitle();
	rename(rstr);
}
