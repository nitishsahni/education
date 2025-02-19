import streamlit as st
from datetime import date, timedelta
import numpy as np

# Constants
STOCKS_RETURN = 0.113
BONDS_RETURN = 0.046
CASH_RETURN = 0.041
RISK_FREE_RATE = 0.02
STOCKS_VOLATILITY = 0.15
BONDS_VOLATILITY = 0.05
CASH_VOLATILITY = 0.02
CUSHION_PERCENTAGE = 0.15  # 15% cushion

# Portfolio allocation constants
START_ALLOCATION = {
    'stocks': 59,
    'bonds': 41,
    'cash': 0
}

END_ALLOCATION = {
    'stocks': 20,
    'bonds': 43,
    'cash': 37
}

def generate_glide_path(time_horizon: int):
    """Generate a glide path for portfolio allocation."""
    glide_path = []
    for year in range(time_horizon + 1):
        stocks = START_ALLOCATION['stocks'] + (END_ALLOCATION['stocks'] - START_ALLOCATION['stocks']) * year / time_horizon
        bonds = START_ALLOCATION['bonds'] + (END_ALLOCATION['bonds'] - START_ALLOCATION['bonds']) * year / time_horizon
        cash = START_ALLOCATION['cash'] + (END_ALLOCATION['cash'] - START_ALLOCATION['cash']) * year / time_horizon
        glide_path.append({
            'year': year,
            'stocks': round(stocks, 2),
            'bonds': round(bonds, 2),
            'cash': round(cash, 2)
        })
    return glide_path

def calculate_required_deposit(goal: float, years: int, weighted_return: float) -> float:
    """Calculate required annual deposit based on goal and returns."""
    if years <= 0:
        return goal
    
    guess = goal / years
    
    def calculate_final_value(deposit: float) -> float:
        value = 0
        for _ in range(years):
            value += deposit
            stocks = value * (START_ALLOCATION['stocks'] / 100) * (1 + STOCKS_RETURN)
            bonds = value * (START_ALLOCATION['bonds'] / 100) * (1 + BONDS_RETURN)
            cash = value * (START_ALLOCATION['cash'] / 100) * (1 + CASH_RETURN)
            value = stocks + bonds + cash
        return value
    
    low, high = 0, goal * 2
    for _ in range(20):  # Binary search for optimal deposit
        guess = (low + high) / 2
        final_value = calculate_final_value(guess)
        if abs(final_value - goal) < 0.01:
            break
        if final_value < goal:
            low = guess
        else:
            high = guess
    return guess

def calculate_portfolio_projections(annual_deposit: float, time_horizon: int, glide_path):
    """Calculate year-by-year portfolio projections."""
    projections = []
    portfolio_value = 0
    
    for year in range(1, time_horizon + 1):
        # Add annual deposit
        portfolio_value += annual_deposit
        
        # Get current year's allocation
        allocation = glide_path[year - 1]
        
        # Calculate individual asset values
        stocks_value = portfolio_value * (allocation['stocks'] / 100)
        bonds_value = portfolio_value * (allocation['bonds'] / 100)
        cash_value = portfolio_value * (allocation['cash'] / 100)
        
        # Apply returns
        stocks_after_return = stocks_value * (1 + STOCKS_RETURN)
        bonds_after_return = bonds_value * (1 + BONDS_RETURN)
        cash_after_return = cash_value * (1 + CASH_RETURN)
        
        # Update portfolio value
        portfolio_value = stocks_after_return + bonds_after_return + cash_after_return
        
        projections.append({
            'year': year,
            'deposit': annual_deposit,
            'portfolio_value': portfolio_value,
            'stocks_value': stocks_after_return,
            'bonds_value': bonds_after_return,
            'cash_value': cash_after_return
        })
    
    return projections

def main():
    st.title("Education Savings Calculator")
    
    # Input form
    with st.form("savings_calculator"):
        annual_tuition = st.number_input(
            "Annual Tuition Cost ($)",
            min_value=0.0,
            value=20000.0,
            step=1000.0
        )
        
        years_in_university = st.number_input(
            "Number of Years in University",
            min_value=1,
            max_value=10,
            value=4
        )
        
        start_date = st.date_input(
            "When do you want to start saving?",
            min_value=date.today(),
            value=date.today()
        )
        
        university_start_date = st.date_input(
            "When does university start?",
            min_value=date.today(),
            value=date.today() + timedelta(days=365*4)
        )
        
        inflation_rate = st.slider(
            "Expected Annual Inflation Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=2.0,
            step=0.1
        ) / 100
        
        submitted = st.form_submit_button("Calculate Savings Plan")
    
    if submitted:
        if start_date >= university_start_date:
            st.error("Start date must be before university start date")
            return
        
        # Calculate time horizon
        time_horizon = round((university_start_date - start_date).days / 365.25)
        
        # Calculate total tuition cost
        total_tuition = annual_tuition * years_in_university
        
        # Calculate cushion (15% of total tuition)
        cushion_savings = total_tuition * CUSHION_PERCENTAGE
        
        # Calculate total savings goal
        total_savings_goal = total_tuition + cushion_savings
        
        # Generate glide path
        glide_path = generate_glide_path(time_horizon)
        
        # Calculate weighted return
        initial_allocation = glide_path[0]
        weighted_return = (
            STOCKS_RETURN * initial_allocation['stocks']/100 +
            BONDS_RETURN * initial_allocation['bonds']/100 +
            CASH_RETURN * initial_allocation['cash']/100
        )
        
        # Calculate recommended deposit
        recommended_deposit = calculate_required_deposit(
            total_savings_goal,
            time_horizon,
            weighted_return
        )
        
        # Calculate projections
        projections = calculate_portfolio_projections(
            recommended_deposit,
            time_horizon,
            glide_path
        )
        
        # Display results
        st.header("Savings Plan Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Annual Deposit Needed", f"${recommended_deposit:,.2f}")
        with col2:
            st.metric("Total Savings Goal", f"${total_savings_goal:,.2f}")
        with col3:
            st.metric("Time Horizon", f"{time_horizon} years")
        
        # Display portfolio projections
        st.subheader("Year-by-Year Projections")
        projection_data = []
        for p in projections:
            projection_data.append({
                "Year": p['year'],
                "Annual Deposit": f"${p['deposit']:,.2f}",
                "Portfolio Value": f"${p['portfolio_value']:,.2f}",
                "Stocks": f"${p['stocks_value']:,.2f}",
                "Bonds": f"${p['bonds_value']:,.2f}",
                "Cash": f"${p['cash_value']:,.2f}"
            })
        st.dataframe(projection_data)
        
        # Display glide path
        st.subheader("Investment Allocation Over Time")
        glide_path_data = []
        for g in glide_path:
            glide_path_data.append({
                "Year": g['year'],
                "Stocks (%)": f"{g['stocks']:.1f}%",
                "Bonds (%)": f"{g['bonds']:.1f}%",
                "Cash (%)": f"{g['cash']:.1f}%"
            })
        st.dataframe(glide_path_data)

if __name__ == "__main__":
    main()
