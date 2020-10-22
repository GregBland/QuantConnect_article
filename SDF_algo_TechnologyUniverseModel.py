from Selection.FundamentalUniverseSelectionModel import FundamentalUniverseSelectionModel


class TechnologyUniverseModule(FundamentalUniverseSelectionModel):
    '''
    This module selects the most liquid stocks listed on the Nasdaq Stock Exchange.
    '''

    def __init__(self, filterFineData=True, universeSettings=None, securityInitializer=None):
        '''Initializes a new default instance of the TechnologyUniverseModule'''
        super().__init__(filterFineData, universeSettings, securityInitializer)
        self.numberOfSymbolsCoarse = 1000
        self.numberOfSymbolsFine = 100
        self.dollarVolumeBySymbol = {}
        self.lastMonth = -1

    def SelectCoarse(self, algorithm, coarse):
        '''
        Performs a coarse selection:

        -The stock must have fundamental data
        -The stock must have positive previous-day close price
        -The stock must have positive volume on the previous trading day
        '''
        if algorithm.Time.month == self.lastMonth:
            return Universe.Unchanged

        sortedByDollarVolume = sorted([x for x in coarse if x.HasFundamentalData and x.Volume > 0 and x.Price > 0],
                                      key=lambda x: x.DollarVolume, reverse=True)[:self.numberOfSymbolsCoarse]

        self.dollarVolumeBySymbol = {x.Symbol: x.DollarVolume for x in sortedByDollarVolume}

        # If no security has met the QC500 criteria, the universe is unchanged.
        if len(self.dollarVolumeBySymbol) == 0:
            return Universe.Unchanged

        return list(self.dollarVolumeBySymbol.keys())

    def SelectFine(self, algorithm, fine):
        '''
        Performs a fine selection:

        -The company's headquarter must in the U.S.
        -The stock must be traded on the NASDAQ stock exchange
        -The stock must be in the Industry Template Code catagory N
        -At least half a year since its initial public offering
        '''
        # Filter stocks and sort on dollar volume
        sortedByDollarVolume = sorted([x for x in fine if x.CompanyReference.CountryId == "USA"
                                       and x.CompanyReference.PrimaryExchangeID == "NAS"
                                       and x.CompanyReference.IndustryTemplateCode == "N"
                                       and (algorithm.Time - x.SecurityReference.IPODate).days > 180],
                                      key=lambda x: self.dollarVolumeBySymbol[x.Symbol], reverse=True)

        if len(sortedByDollarVolume) == 0:
            return Universe.Unchanged

        self.lastMonth = algorithm.Time.month

        return [x.Symbol for x in sortedByDollarVolume[:self.numberOfSymbolsFine]]