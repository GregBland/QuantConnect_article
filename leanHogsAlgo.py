import pandas as pd


class LeanHogsBollingerBandsAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2015, 1, 1)  # Set Start Date
        self.SetEndDate(2020, 6, 1)  # Set End Date
        self.SetCash(100000)  # Set Strategy Cash

        self.new_day = True
        self.contract = None

        # Subscribe and set our expiry filter for the futures chain
        futureES = self.AddFuture(Futures.Meats.LeanHogs)
        futureES.SetFilter(TimeSpan.FromDays(30), TimeSpan.FromDays(720))

    def OnData(self, slice):

        self.InitUpdateContract(slice)

    def InitUpdateContract(self, slice):
        # Reset daily - everyday we check whether futures need to be rolled
        if not self.new_day:
            return

        if self.contract != None and (self.contract.Expiry - self.Time).days >= 3:  # rolling 3 days before expiry
            return

        for chain in slice.FutureChains.Values:
            # If we trading a contract, send to log how many days until the contract's expiry
            if self.contract != None:
                self.Log(
                    'Expiry days away {} - {}'.format((self.contract.Expiry - self.Time).days, self.contract.Expiry))

                # Reset any open positions based on a contract rollover.
                self.Log('RESET: closing all positions')
                self.Liquidate()

            # get list of contracts
            contracts = list(chain.Contracts.Values)
            chain_contracts = list(contracts)  # [contract for contract in chain]
            # order list of contracts by expiry date: newest --> oldest
            chain_contracts = sorted(chain_contracts, key=lambda x: x.Expiry)

            # pick out contract and log contract name
            self.contract = chain_contracts[1]
            self.Log("Setting contract to: {}".format(self.contract.Symbol.Value))

            # Set up consolidators.
            one_hour = TradeBarConsolidator(TimeSpan.FromMinutes(60))
            one_hour.DataConsolidated += self.OnHour

            self.SubscriptionManager.AddConsolidator(self.contract.Symbol, one_hour)

            # Set up indicators
            self.Bolband = self.BB(self.contract.Symbol, 50, 2, MovingAverageType.Simple, Resolution.Hour)

            history = self.History(self.contract.Symbol, 50 * 60, Resolution.Minute).reset_index(drop=False)

            for bar in history.itertuples():
                if bar.time.minute == 0 and ((self.Time - bar.time) / pd.Timedelta(minutes=1)) >= 2:
                    self.Bolband.Update(bar.time, bar.close)

            self.new_day = False

    def OnHour(self, sender, bar):

        if (self.Bolband != None and self.Bolband.IsReady):
            if bar.Symbol == self.contract.Symbol:
                price = bar.Close

                holdings = self.Portfolio[self.contract.Symbol].Quantity

                # buy if price closes below lower bollinger band
                if holdings <= 0 and price < self.Bolband.LowerBand.Current.Value:
                    self.Log("BUY >> {}".format(price))
                    self.MarketOrder(self.contract.Symbol, 2)

                # sell if price closes above the upper bollinger band
                if holdings > 0 and price > self.Bolband.UpperBand.Current.Value:
                    self.Log("SELL >> {}".format(price))
                    self.Liquidate()

            self.Plot("BB", "MiddleBand", self.Bolband.MiddleBand.Current.Value)
            self.Plot("BB", "UpperBand", self.Bolband.UpperBand.Current.Value)
            self.Plot("BB", "LowerBand", self.Bolband.LowerBand.Current.Value)

        else:
            self.Log('Bollinger Bands not ready yet')

    def OnEndOfDay(self):
        self.new_day = True