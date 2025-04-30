import matplotlib.pyplot as plt

LOW_STOCK_THRESHOLD = 20  # Make threshold configurable here - default value

def display_medication_stock_dashboard(stock, low_stock_threshold=LOW_STOCK_THRESHOLD): # Pass threshold as argument
    """Displays medication stock dashboard using matplotlib, highlighting low stock based on configurable threshold."""
    if not stock:
        print("No medication stock data available to display.")
        return

    med_names = list(stock.keys())
    quantities = list(stock.values())

    # Determine low stock medications using configurable threshold
    low_stock_meds_indices = [i for i, qty in enumerate(quantities) if qty < low_stock_threshold]
    bar_colors = ['blue'] * len(med_names) # Default colors
    for index in low_stock_meds_indices:
        bar_colors[index] = 'red' # Highlight low stock in red

    plt.figure(figsize=(10, 6))
    bars = plt.bar(med_names, quantities, color=bar_colors) # Apply colors to bars
    plt.xlabel("Medication Name")
    plt.ylabel("Stock Quantity")
    plt.title("Medication Stock Levels")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Add stock count labels on top of bars, highlight low stock counts
    for bar_index, bar in enumerate(bars):
        height = bar.get_height()
        label_color = 'black' # Default color for label
        if bar_index in low_stock_meds_indices:
            label_color = 'red' # Red label for low stock

        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{quantities[bar_index]}',
                ha='center', va='bottom', color=label_color, fontweight='bold') # Bold, colored count

    # Add annotations for low stock medications
    if low_stock_meds_indices:
        low_stock_names = [med_names[i] for i in low_stock_meds_indices]
        low_stock_counts = [quantities[i] for i in low_stock_meds_indices]
        annotation_text = "⚠️ Low Stock Medications (Quantity < {}):\n".format(low_stock_threshold) # Indicate threshold in annotation
        for i in range(len(low_stock_names)):
            annotation_text += f"- {low_stock_names[i]} : {low_stock_counts[i]}\n"

        plt.annotate(annotation_text.strip(), # Remove trailing newline
                     xy=(0.98, 0.98), xycoords='axes fraction',
                     ha='right', va='top',
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.5)) # Yellow box

    plt.show()