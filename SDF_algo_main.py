from SmartInsiderAlphaModel import SmartInsiderAlphaModel
from Execution.ImmediateExecutionModel import ImmediateExecutionModel
from TechnologyUniverseModule import TechnologyUniverseModule


class SDFDemoAlgo(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2018, 1, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        # self.AddEquity("SPY", Resolution.Minute)
        self.AddAlpha(SmartInsiderAlphaModel())

        self.SetExecution(ImmediateExecutionModel())

        self.SetPortfolioConstruction(InsightWeightingPortfolioConstructionModel())

        self.SetRiskManagement(MaximumDrawdownPercentPortfolio(0.03))

        self.SetUniverseSelection(TechnologyUniverseModule())

    def OnData(self, data):
        pass

