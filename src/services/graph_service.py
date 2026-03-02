"""
Graph generation service using matplotlib
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Optional
import io
from src.models.schemas import HistoryEntry


class GraphService:
    """Service for generating graphs and charts"""
    
    def __init__(self):
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def generate_calorie_trend_graph(
        self,
        history: List[HistoryEntry],
        title: str = "Calorie Trend"
    ) -> Optional[io.BytesIO]:
        """
        Generate a calorie trend line graph
        Returns: BytesIO object containing PNG image
        """
        if not history or all(h.entry_count == 0 for h in history):
            return None
        
        # Filter out days with no entries and sort by date
        data = [h for h in history if h.entry_count > 0]
        data.sort(key=lambda x: x.date)
        
        if not data:
            return None
        
        # Extract data
        dates = [h.date for h in data]
        calories = [h.calories for h in data]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot line
        ax.plot(dates, calories, marker='o', linewidth=2, markersize=8, 
                color='#2E86AB', label='Daily Calories')
        
        # Add average line
        avg_calories = sum(calories) / len(calories)
        ax.axhline(y=avg_calories, color='#A23B72', linestyle='--', 
                   linewidth=2, label=f'Average: {avg_calories:.0f} kcal')
        
        # Formatting
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Calories (kcal)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        plt.xticks(rotation=45, ha='right')
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Legend
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Add value labels on points
        for date, cal in zip(dates, calories):
            ax.annotate(f'{cal:.0f}', 
                       xy=(date, cal), 
                       xytext=(0, 10),
                       textcoords='offset points',
                       ha='center',
                       fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', 
                                facecolor='white', 
                                edgecolor='gray',
                                alpha=0.7))
        
        # Tight layout
        plt.tight_layout()
        
        # Save to BytesIO
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    
    def generate_macro_distribution_pie(
        self,
        protein: float,
        carbs: float,
        fats: float,
        title: str = "Macro Distribution"
    ) -> Optional[io.BytesIO]:
        """
        Generate a pie chart showing macro distribution
        Returns: BytesIO object containing PNG image
        """
        if protein == 0 and carbs == 0 and fats == 0:
            return None
        
        # Calculate calories from macros
        protein_cals = protein * 4
        carbs_cals = carbs * 4
        fats_cals = fats * 9
        
        total_cals = protein_cals + carbs_cals + fats_cals
        
        if total_cals == 0:
            return None
        
        # Data
        sizes = [protein_cals, carbs_cals, fats_cals]
        labels = [
            f'Protein\n{protein:.1f}g ({protein_cals/total_cals*100:.1f}%)',
            f'Carbs\n{carbs:.1f}g ({carbs_cals/total_cals*100:.1f}%)',
            f'Fats\n{fats:.1f}g ({fats_cals/total_cals*100:.1f}%)'
        ]
        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D']
        explode = (0.05, 0.05, 0.05)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot pie chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            shadow=True,
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )
        
        # Make percentage text white and bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
            autotext.set_fontweight('bold')
        
        # Title
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Equal aspect ratio ensures circular pie
        ax.axis('equal')
        
        # Save to BytesIO
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    
    def generate_weekly_comparison_bar(
        self,
        history: List[HistoryEntry],
        title: str = "Weekly Calorie Comparison"
    ) -> Optional[io.BytesIO]:
        """
        Generate a bar chart comparing daily calories
        Returns: BytesIO object containing PNG image
        """
        if not history or all(h.entry_count == 0 for h in history):
            return None
        
        # Filter and sort
        data = [h for h in history if h.entry_count > 0]
        data.sort(key=lambda x: x.date)
        
        if not data:
            return None
        
        # Extract data
        dates = [h.date.strftime('%a\n%b %d') for h in data]
        calories = [h.calories for h in data]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create bars with gradient colors
        bars = ax.bar(dates, calories, color='#2E86AB', alpha=0.8, edgecolor='black')
        
        # Color bars based on value (gradient effect)
        avg_cal = sum(calories) / len(calories)
        for bar, cal in zip(bars, calories):
            if cal > avg_cal:
                bar.set_color('#27AE60')  # Green for above average
            else:
                bar.set_color('#E74C3C')  # Red for below average
        
        # Add average line
        ax.axhline(y=avg_cal, color='#F39C12', linestyle='--', 
                   linewidth=2, label=f'Average: {avg_cal:.0f} kcal')
        
        # Add value labels on bars
        for i, (bar, cal) in enumerate(zip(bars, calories)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{cal:.0f}',
                   ha='center', va='bottom',
                   fontsize=10, fontweight='bold')
        
        # Formatting
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Calories (kcal)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Grid
        ax.grid(True, alpha=0.3, axis='y')
        
        # Legend
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Tight layout
        plt.tight_layout()
        
        # Save to BytesIO
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf

# Made with Bob
