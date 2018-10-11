import pandas as pd

def simulate_retirement(df, savings, initial_withdrawal_rate,
                        adjustment_withdrawal_rate, retirement_length, 
                        initial_equity_weight, equity_glide_adjustment,
                        success_rule=1):
    """A function to simulate the outcome of retirement portfolios and spending plans.

    The function uses the provided parameters to simulate how a simple retirement
    portfolio would perform starting from each month of available data.
    
    The portfolio is invested in the the S&P 500 and the 10-year treasury bond 
    according to the initial_equity_weight parameter. The value of withdrawals 
    is set according to initial_withdrawal_rate. Over time, withdrawals are adjusted 
    for inflation and the equity weight is increased gradually toward 1 according to 
    the equity_glide_adjustment parameter.
    
    adjustment_withdrawal_rate is the rate at which withdrawals can safely be 
    adjusted upward (in addition to inflation adjustments) after retirement begins. 
    i.e. If your spending falls below this rate relative to the portfolio value, 
    you can safely adjust upward and reset the equity glide path.
    """
    
    portfolio_preservation = []
    portfolio_survival = []

    nominalyield = df.SPNominalYield.tolist()
    dividendyield = df.SPDividendYield.tolist()
    bondyield = df.TenYearBondReturn.tolist()
    inflation = df.Inflation.tolist()

    for retirement_year in range(0, len(df) - retirement_length + 1):
        balance = savings
        income = (initial_withdrawal_rate/12)*savings
        inflation_factor = 1.0
        equity_weight = initial_equity_weight
        for w, x, y, z in zip(nominalyield[retirement_year:(retirement_year + retirement_length - 1)], \
                              dividendyield[retirement_year:(retirement_year + retirement_length - 1)], \
                              bondyield[retirement_year:(retirement_year + retirement_length - 1)], \
                              inflation[retirement_year:(retirement_year + retirement_length - 1)]):
            income *= (1 + z)
            balance = balance*(equity_weight*(1 + w)*(1 + x) + (1 - equity_weight)*(1 + y)) - income
            inflation_factor *= (1 + z)
            if equity_weight < 1:
                equity_weight += min(equity_glide_adjustment, 1 - equity_weight)
            if income < (adjustment_withdrawal_rate)*balance/12:
                income = (adjustment_withdrawal_rate)*balance/12
                equity_weight = initial_equity_weight
        portfolio_preservation.append(balance > inflation_factor*savings)
        portfolio_survival.append(balance > 0)

    if success_rule == 0:
        return all(portfolio_survival)
    elif success_rule == 1:
        return all(portfolio_preservation)
    else:
        raise ValueError('Invalid success rule.')


def find_solutions(df, savings, retirement_length, initial_equity_weight, 
                   equity_glide_adjustment, success_rule=1):
    """A function to find the maximum safe withdrawal & safe adjustment rates.
    
    The function finds the withdrawal rates (between 0% and 100%) at which the 
    portfolio maintains a positive balance (success_rule = 0) or maintains the
    inflation adjusted original balance (success_rule = 1) for all given retirement dates.
    """

    rate_a = 0.0
    rate_b = 1.0
    while rate_b - rate_a > 0.00005:
        rate_c = (rate_a + rate_b)/2
        if simulate_retirement(df, savings, rate_c, 0, retirement_length, 
                               initial_equity_weight, equity_glide_adjustment,
                               success_rule):
            rate_a = rate_c
        else:
            rate_b = rate_c
    safe_withdrawal_rate = int(rate_c*10000)/10000.0 # Round down to 4 dec places

    adjustment_rate_a = 0.0
    adjustment_rate_b = 1.0
    while adjustment_rate_b - adjustment_rate_a > 0.00005:
        adjustment_rate_c = (adjustment_rate_a + adjustment_rate_b)/2
        if simulate_retirement(df, savings, safe_withdrawal_rate, adjustment_rate_c, 
                               retirement_length, initial_equity_weight, 
                               equity_glide_adjustment, success_rule):
            adjustment_rate_a = adjustment_rate_c
        else:
            adjustment_rate_b = adjustment_rate_c
    safe_adjustment_rate = int(adjustment_rate_c*10000)/10000.0

    return safe_withdrawal_rate, safe_adjustment_rate


if __name__ == '__main__':
    df = pd.read_csv('historical_market_data.csv')
    solution_rate, solution_adjustment_rate = find_solutions(df, 100000, 720, 0.6, 0.005, 1)
    print(solution_rate)
    print(solution_adjustment_rate)
