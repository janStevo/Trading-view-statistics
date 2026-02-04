# derrived from OpenPositionsStatistics_02
# compare multiple startegies combinations
import polars as pl
from datetime import *
from time import sleep
import matplotlib
matplotlib.use('TkAgg')  # or 'Qt5Agg' if you have Qt installed
import matplotlib.pyplot as plt
from pathlib import Path

class CONST():
    # static attributes
    ENTRY_LONG = "Entry long"
    EXIT_LONG = "Exit long"
    ENTRY_SHORT = "Entry short"
    EXIT_SHORT = "Exit short"
    FOLDER_PATH = Path("trades_data02")
    FEE = 0 # 0.00055

class PARAM():
    # static attributes
    STRAT_VAL = 1000
    INVESTMENT: int = None
    ALL_POSITIONS: int = None
    FOLDERS = {Path("test_sharing_capital"): 1000} # the value is a 1 strategy investment

class Statistics():

    def mainLoop(self):
        lFigures = []
        for folder, stratVal in PARAM.FOLDERS.items():
            PARAM.STRAT_VAL = stratVal
            lProfits, lPositions = self.getChartData(iFolder=folder, iMaxPos=None)
            lFigures.append(self.getPlotChart(iData=[lProfits, lPositions], iMaxPos=None))
        for fig in lFigures:
            plt.show(block=True)

    def getChartData(self, iMaxPos:int=None, iMartiangle=False, iFolder=CONST.FOLDER_PATH): # SJ6toDo: implement monte carlo analysis for trades order
                                                                 # SJ6toDo: implement plotting by date
        ldfAllData = pl.DataFrame()
        # Loop through all files in the folder
        j = 0
        for file in iFolder.iterdir():
            if file.is_file():  # Check if it's a file
                j += 1 # testing data: It was put into this condition (if block)
                lInputFile = iFolder.name + "/" + file.name
                # <--2025-04-12 - SJ6 - an update on tradingview, the files are of type .xlsx
                # ldfExcelData = pl.read_csv(lInputFile, has_header=True)
                ldfExcelData = pl.read_excel(lInputFile, sheet_name="List of trades", has_header=True)
                # SJ6-->
                ldfExcelData = ldfExcelData.with_columns(pl.lit(j).alias("fileId"))
                if "Price" in ldfExcelData.columns:
                    ldfExcelData = ldfExcelData.rename({"Price": "Price USDT"})
                if ldfExcelData.schema[ldfExcelData.columns[3]] == pl.Date:
                    ldfExcelData = ldfExcelData.with_columns(ldfExcelData[ldfExcelData.columns[3]].cast(pl.Datetime(time_unit="ms")))
                if ldfExcelData.schema[ldfExcelData.columns[5]] == pl.Int64:
                    # Convert the fifth column to Float64
                    ldfExcelData = ldfExcelData.with_columns(ldfExcelData[ldfExcelData.columns[5]].cast(pl.Float64))
                if ldfExcelData.schema[ldfExcelData.columns[4]] == pl.String:
                    ldfExcelData = ldfExcelData.with_columns(
                        pl.col("Price USDT").str.replace_all(",", "").alias("Price USDT")
                    )
                    # Convert the fourth column to Float64
                    ldfExcelData = ldfExcelData.with_columns(ldfExcelData[ldfExcelData.columns[4]].cast(pl.Float64))
                ldfAllData = pl.concat([ldfAllData, ldfExcelData])
        PARAM.ALL_POSITIONS = j
        PARAM.INVESTMENT = j*PARAM.STRAT_VAL
        # ldfAllData = ldfAllData.with_columns(
        #     pl.col("Date/Time").str.strptime(pl.Datetime, format="%Y-%m-%d %H:%M").alias("Date/Time")
        # )

        ldfAllData = ldfAllData.with_columns(
            pl.when(pl.col("Type") == "Entry Long").then(0)
            .when(pl.col("Type") == "Entry Short").then(1)
            .when(pl.col("Type") == "Exit Long").then(2)
            .when(pl.col("Type") == "Exit Short").then(3)
            .otherwise(None).alias("type_order")
        )
        ldfAllData = ldfAllData.sort(["Date/Time", "type_order"])
        ldfAllData = ldfAllData.drop("type_order")
        ldfAllData = ldfAllData.filter((ldfAllData[ldfAllData.columns[2]] != "Open") & (ldfAllData[ldfAllData.columns[5]].is_not_nan()))
        #                   0       1       2       3               4           5           6           7               8               9               10          11          12              13          14
        # the form is: | Trade# | Type | Signal | Date/Time | Price USDT | Contracts | Profit USDT | Profit % | Cum. Profit USDT | Cum. Profit % | Run-up USDT | Run-up % | Drawdown USDT | Drawdown % | fileId |

        lOpen: int = 0
        lProfits = []
        lPositions = []
        lProfit = 0
        lEntry = {}
        lTime = datetime(1,1,1)
        if iMartiangle:
            lCurCap = PARAM.INVESTMENT
            if iMaxPos == None:
                for order in ldfAllData.iter_rows():
                    if lTime < order[3]:
                        lPositions.append(lOpen)
                        lProfits.append(lProfit)
                        lProfit = 0
                        lTime = order[3]
                    if order[1] == CONST.ENTRY_LONG:
                        if order[-1] == 13:
                            lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/3*2
                        elif order[-1] in [7,8,9,17,18,19]:
                            lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/3
                        else:
                            lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/2
                        lEntry[(order[0], order[14])] = {"price":order[4], "qty":lQty}
                        lOpen += 1
                        lProfit -= (order[4]*lQty)*CONST.FEE
                        lCurCap -= (order[4]*lQty)*CONST.FEE
                    elif order[1] == CONST.EXIT_LONG:
                        lOpen -= 1
                        lPos = lEntry.pop((order[0], order[14]))
                        lProfit += lPos["qty"]*(order[4] - lPos["price"])
                        lCurCap += lPos["qty"]*(order[4] - lPos["price"])
                        lProfit -= (order[4]*lPos["qty"])*CONST.FEE
                        lCurCap -= (order[4]*lPos["qty"])*CONST.FEE
                    elif order[1] == CONST.ENTRY_SHORT:
                        if order[-1] == 13:
                            lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/3*2
                        elif order[-1] in [7,8,9,17,18,19]:
                            lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/3
                        else:
                            lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/2
                        lEntry[(order[0], order[14])] = {"price":order[4], "qty":lQty}
                        lOpen += 1
                        lProfit -= (order[4]*lQty)*CONST.FEE
                        lCurCap -= (order[4]*lQty)*CONST.FEE
                    elif order[1] == CONST.EXIT_SHORT:
                        lOpen -= 1
                        lPos = lEntry.pop((order[0], order[14]))
                        lProfit += lPos["qty"]*(-order[4] + lPos["price"])
                        lCurCap += lPos["qty"]*(-order[4] + lPos["price"])
                        lProfit -= (order[4]*lPos["qty"])*CONST.FEE
                        lCurCap -= (order[4]*lPos["qty"])*CONST.FEE
                lPositions.append(lOpen)
                lProfits.append(lProfit)
            else:
                lDisabled = []
                for order in ldfAllData.iter_rows():
                    if lTime < order[3]:
                        lPositions.append(lOpen)
                        lProfits.append(lProfit)
                        lProfit = 0
                        lTime = order[3]
                    if order[1] == CONST.ENTRY_LONG:
                        if lOpen + 1 > iMaxPos:
                            lDisabled.append((order[0], order[-1]))
                        else:
                            if order[-1] == 13:
                                lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/3*2
                            elif order[-1] in [7,8,9,17,18,19]:
                                lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/3
                            else:
                                lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/2
                            lQty = lQty*(2 - (iMaxPos)/PARAM.ALL_POSITIONS)
                            lEntry[(order[0], order[14])] = {"price":order[4], "qty":lQty}
                            lOpen += 1
                            lProfit -= (order[4]*lQty)*CONST.FEE
                            lCurCap -= (order[4]*lQty)*CONST.FEE
                    elif order[1] == CONST.EXIT_LONG:
                        item = None
                        for i in range(len(lDisabled)):
                            if lDisabled[i] == (order[0], order[-1]):
                                item = lDisabled.pop(i)
                                break
                        if item == None:
                            lOpen -= 1
                            lPos = lEntry.pop((order[0], order[14]))
                            lProfit += lPos["qty"]*(order[4] - lPos["price"])
                            lCurCap += lPos["qty"]*(order[4] - lPos["price"])
                            lProfit -= (order[4]*lPos["qty"])*CONST.FEE
                            lCurCap -= (order[4]*lPos["qty"])*CONST.FEE
                    elif order[1] == CONST.ENTRY_SHORT:
                        if lOpen + 1 > iMaxPos:
                            lDisabled.append((order[0], order[-1]))
                        else:
                            if order[-1] == 13:
                                lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/3*2
                            elif order[-1] in [7,8,9,17,18,19]:
                                lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/3
                            else:
                                lQty = lCurCap/PARAM.ALL_POSITIONS/order[4]/2
                            lQty = lQty*(2 - (iMaxPos)/PARAM.ALL_POSITIONS)
                            lEntry[(order[0], order[14])] = {"price":order[4], "qty":lQty}
                            lOpen += 1
                            lProfit -= (order[4]*lQty)*CONST.FEE
                            lCurCap -= (order[4]*lQty)*CONST.FEE
                    elif order[1] == CONST.EXIT_SHORT:
                        item = None
                        for i in range(len(lDisabled)):
                            if lDisabled[i] == (order[0], order[-1]):
                                item = lDisabled.pop(i)
                                break
                        if item == None:
                            lOpen -= 1
                            lPos = lEntry.pop((order[0], order[14]))
                            lProfit += lPos["qty"]*(-order[4] + lPos["price"])
                            lCurCap += lPos["qty"]*(-order[4] + lPos["price"])
                            lProfit -= (order[4]*lPos["qty"])*CONST.FEE
                            lCurCap -= (order[4]*lPos["qty"])*CONST.FEE
                lPositions.append(lOpen)
                lProfits.append(lProfit)
        else:
            if iMaxPos == None:
                for order in ldfAllData.iter_rows():
                    if isinstance(order[3], date):
                        lOrderTime = datetime(order[3].year, order[3].month, order[3].day)
                    else:
                        lOrderTime = order[3]
                    if lTime < lOrderTime:
                        lPositions.append(lOpen)
                        lProfits.append(lProfit)
                        lProfit = 0
                        lTime = lOrderTime
                    if order[1] == CONST.ENTRY_LONG:
                        lOpen += 1
                    elif order[1] == CONST.EXIT_LONG:
                        lOpen -= 1
                        lProfit += order[6]
                    elif order[1] == CONST.ENTRY_SHORT:
                        lOpen += 1
                    elif order[1] == CONST.EXIT_SHORT:
                        lOpen -= 1
                        lProfit += order[6]
                    lProfit -= (order[4]*order[5])*CONST.FEE
                lPositions.append(lOpen)
                lProfits.append(lProfit)
            else: # if there is not enough capital at the time of position opening, the position will not happen any time later
                lDisabled = []
                for order in ldfAllData.iter_rows():
                    if isinstance(order[3], date):
                        lOrderTime = datetime(order[3].year, order[3].month, order[3].day)
                    else:
                        lOrderTime = order[3]
                    if lTime < lOrderTime:
                        lPositions.append(lOpen)
                        lProfits.append(lProfit)
                        lProfit = 0
                        lTime = lOrderTime
                    if order[1] == CONST.ENTRY_LONG:
                        if lOpen + 1 > iMaxPos:
                            lDisabled.append((order[0], order[-1]))
                        else:
                            lOpen += 1
                            lProfit -= (order[4]*order[5])*CONST.FEE*(2 - (iMaxPos)/PARAM.ALL_POSITIONS)
                    elif order[1] == CONST.EXIT_LONG:
                        item = None
                        for i in range(len(lDisabled)):
                            if lDisabled[i] == (order[0], order[-1]):
                                item = lDisabled.pop(i)
                                break
                        if item == None:
                            lOpen -= 1
                            lProfit += order[6]*(2 - iMaxPos/PARAM.ALL_POSITIONS)
                            lProfit -= (order[4]*order[5])*CONST.FEE*(2 - (iMaxPos)/PARAM.ALL_POSITIONS)
                    elif order[1] == CONST.ENTRY_SHORT:
                        if lOpen + 1 > iMaxPos:
                            lDisabled.append((order[0], order[-1]))
                        else:
                            lOpen += 1
                            lProfit -= (order[4]*order[5])*CONST.FEE*(2 - (iMaxPos)/PARAM.ALL_POSITIONS)
                    elif order[1] == CONST.EXIT_SHORT:
                        item = None
                        for i in range(len(lDisabled)):
                            if lDisabled[i] == (order[0], order[-1]):
                                item = lDisabled.pop(i)
                                break
                        if item == None:
                            lOpen -= 1
                            lProfit += order[6]*(2 - iMaxPos/PARAM.ALL_POSITIONS)
                            lProfit -= (order[4]*order[5])*CONST.FEE*(2 - (iMaxPos)/PARAM.ALL_POSITIONS)
                lPositions.append(lOpen)
                lProfits.append(lProfit)
        return lProfits, lPositions
    
    def calcDrawdowns(self, iProfits):
        lDrawdowns = []
        lPeak = None
        lMaxDrawdown = 0
        for profit in iProfits:
            if lPeak == None:
                lPeak = profit
                lDrawdowns.append(0)
            else:
                if profit >= lPeak:
                    lDrawdowns.append(0)
                    lPeak = profit
                else:
                    lDrawdowns.append(lPeak - profit)
                    lMaxDrawdown = max(lMaxDrawdown, lDrawdowns[-1])
        return lDrawdowns, lMaxDrawdown
    
    def getPlotChart(self, iData: list, iMaxPos=None, iInvestment=None):
        lInvestment = iInvestment if iInvestment is not None else PARAM.INVESTMENT

        # Data for the first chart
        lProfits = iData[0]
        lLastProfit = None
        y1 = [lInvestment,]
        for profit in lProfits:
            if lLastProfit is None:
                lLastProfit = profit + lInvestment
            else:
                lLastProfit += profit
            y1.append(lLastProfit)
        x1 = [x for x in range(1, len(y1) + 1)]

        yDrawdown, lMaxDrawdown = self.calcDrawdowns(y1)

        # Data for the second chart
        if len(iData) > 1:
            lSecondaryData = iData[1]
            x2 = [x for x in range(1, len(lSecondaryData) + 1)]
            y2 = lSecondaryData
        else:
            raise ValueError("iData[1] is missing for the second chart!")

        # Create subplots
        fig, axes = plt.subplots(2, 1, figsize=(8, 8))  # 2 rows, 1 column

        # First subplot: Plot profits
        # axes[0].bar(x1, yDrawdown, label="Drawdowns", color="orange", alpha=0.5)
        axes[0].plot(x1, y1, label='Cumulative Profits', color='blue', marker='o')
        axes[0].set_xlabel('trades')
        axes[0].set_ylabel('profit')
        axes[0].set_title(f'Profit={lLastProfit-PARAM.INVESTMENT}, max drawdown={lMaxDrawdown}, ret/DD ratio={(lLastProfit-PARAM.INVESTMENT)/lMaxDrawdown}')
        axes[0].legend()

        # Create a secondary y-axis
        axesDD = axes[0].twinx()
        axesDD.bar(x1, yDrawdown, label="Drawdowns", color="orange", alpha=0.5)
        axesDD.set_ylabel("drawdown", color="orange")
        axesDD.tick_params(axis="y", labelcolor="orange")

        # Second subplot: Plot secondary data
        axes[1].bar(x2, y2, label='Open positions', color='green', alpha=0.7)
        axes[1].set_xlabel('trades')
        axes[1].set_ylabel('positions')
        axes[1].set_title(f'Max positions={iMaxPos}')
        axes[1].legend()

        # Adjust layout for better spacing
        plt.tight_layout()

        return fig

main = Statistics()
main.mainLoop()