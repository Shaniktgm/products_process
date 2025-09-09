# 🎯 Configurable Scoring System

This system allows you to easily change how products are scored without modifying code. Simply edit the configuration file and run the update script.

## 📁 Files

- **`scoring_config.json`** - Main configuration file
- **`configurable_scoring_system.py`** - Core scoring system
- **`change_scoring_method.py`** - Easy method switcher

## 🚀 Quick Start

### Method 1: Command Line
```bash
# Switch to weighted composite scoring
python3 change_scoring_method.py weighted_composite

# Switch to value-focused scoring  
python3 change_scoring_method.py value_focused

# Switch to luxury premium scoring
python3 change_scoring_method.py luxury_premium

# Switch back to price-based scoring
python3 change_scoring_method.py price_based
```

### Method 2: Interactive Mode
```bash
python3 change_scoring_method.py
```
Then follow the prompts to select your preferred scoring method.

### Method 3: Manual Configuration
1. Edit `scoring_config.json`
2. Change the `"method"` value in `"overall_score"` section
3. Run: `python3 configurable_scoring_system.py`

## 📊 Available Scoring Methods

### 1. **price_based** (Default)
- **Description**: Overall score equals the product price
- **Formula**: `price`
- **Best for**: Simple price-based ranking
- **Range**: 0-1000+

### 2. **weighted_composite**
- **Description**: Weighted combination of all scoring factors
- **Formula**: `total_score * 0.3 + popularity_score * 0.2 + brand_reputation_score * 0.2 + overall_value_score * 0.2 + luxury_score * 0.1`
- **Best for**: Balanced product evaluation
- **Range**: 0-10

### 3. **value_focused**
- **Description**: Focus on value for money (rating/price ratio)
- **Formula**: `(rating * 20) / (price / 10)`
- **Best for**: Finding best value products
- **Range**: 0-100

### 4. **luxury_premium**
- **Description**: Emphasize luxury and premium factors
- **Formula**: `luxury_score * 2 + brand_reputation_score * 1.5 + total_score`
- **Best for**: Premium/luxury product recommendations
- **Range**: 0-30

## ⚙️ Configuration Options

### Scoring Weights (for weighted_composite)
```json
"scoring_weights": {
  "total_score": 0.3,
  "popularity_score": 0.2,
  "brand_reputation_score": 0.2,
  "overall_value_score": 0.2,
  "luxury_score": 0.1
}
```

### Price Categories
```json
"price_categories": {
  "budget": {"max_price": 50, "luxury_multiplier": 0.5},
  "mid_range": {"min_price": 50, "max_price": 150, "luxury_multiplier": 1.0},
  "premium": {"min_price": 150, "max_price": 250, "luxury_multiplier": 1.5},
  "luxury": {"min_price": 250, "luxury_multiplier": 2.0}
}
```

### Material Bonuses
```json
"material_bonuses": {
  "egyptian_cotton": 1.0,
  "bamboo": 0.8,
  "linen": 0.9,
  "silk": 1.2,
  "tencel": 0.7,
  "eucalyptus": 0.6
}
```

## 🔧 Customizing Scoring

### Adding New Methods
1. Edit `scoring_config.json`
2. Add new method to `"overall_score"."options"`
3. Implement the calculation in `configurable_scoring_system.py`

### Modifying Weights
1. Edit `"scoring_weights"` in `scoring_config.json`
2. Run the update script

### Adjusting Thresholds
1. Edit threshold values in `scoring_config.json`
2. Run the update script

## 📈 Example Results

### Price-Based Scoring
- **Top Product**: Signature Hemmed Sheet Set (King) - Score: 299.00
- **Average Score**: 148.12
- **Best for**: Price-conscious customers

### Weighted Composite Scoring  
- **Top Product**: Egyptian Cotton Sheets (1000 Thread) - Score: 9.64
- **Average Score**: 8.40
- **Best for**: Balanced recommendations

### Value-Focused Scoring
- **Top Product**: Twin XL Cotton Velvet Sheets - Score: 100.00
- **Average Score**: 17.18
- **Best for**: Value seekers

### Luxury Premium Scoring
- **Top Product**: Premium luxury sheets - Score: 25.50
- **Average Score**: 18.75
- **Best for**: Luxury market

## 🎯 Use Cases

| Scoring Method | Best For | Customer Type |
|----------------|----------|---------------|
| `price_based` | Budget shopping | Price-conscious |
| `weighted_composite` | General recommendations | Balanced buyers |
| `value_focused` | Best deals | Value seekers |
| `luxury_premium` | High-end products | Luxury buyers |

## 🔄 Workflow

1. **Choose scoring method** based on your target audience
2. **Run the update script** to apply new scoring
3. **Check results** in the summary output
4. **Adjust configuration** if needed
5. **Repeat** as your business needs change

## 💡 Tips

- **Test different methods** to see which works best for your audience
- **Monitor conversion rates** when switching methods
- **A/B test** different scoring approaches
- **Seasonal adjustments** - switch to value-focused during sales
- **Customer segments** - use different methods for different user groups

## 🛠️ Troubleshooting

### Configuration Not Loading
- Check JSON syntax in `scoring_config.json`
- Ensure file exists in the same directory

### Scores Not Updating
- Verify database connection
- Check for errors in the update script output

### Unexpected Results
- Review the scoring formula in configuration
- Check if all required data fields are present

## 📞 Support

If you need help customizing the scoring system:
1. Check the configuration file syntax
2. Review the available methods
3. Test with a small dataset first
4. Monitor the update script output for errors
