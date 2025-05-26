# dataset_information_service_demo_cchstats
以陳傑憲選手2024年12強棒球賽打擊表現演示資料集、資訊提供服務、預測服務與程式的關係

# 復現方法
* [下載本 repository](https://github.com/tingjhenjiang/dataset_information_service_demo_cchstats/archive/refs/heads/main.zip) 程式碼並解壓縮
* [安裝miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install)
* 執行Miniconda powershell，切換至 cchstats 的 conda 環境（ conda activate cchstats ）。miniconda or conda使用可參照 [這裡](https://www.anaconda.com/docs/getting-started/getting-started) 以及 [這裡](https://docs.conda.io/projects/conda/en/stable/user-guide/getting-started.html)
* 切換至程式碼目錄 ( cd 目錄路徑 )
* 透過 conda env create -f cchstats.yml 指令創建環境
* 確定位於 cchstats.py 的目錄後，執行 python cchstats.py
* 在瀏覽器瀏覽 [http://localhost:5000/](http://localhost:5000/)

# Demo
[程式運作實例與說明](https://www.youtube.com/watch?v=Bu6aBD84l4M)