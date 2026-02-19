"""
Nifty Direction Conviction Engine - Layer 3: Options Intelligence
========================================================================
Advanced options chain analysis for Nifty 50 index derivatives.

This module provides comprehensive analysis of options data including:
- Put-Call Ratio (PCR) analysis for sentiment interpretation
- Max Pain calculation for identifying expiry price expectations
- Open Interest (OI) level and buildup tracking
- Integrated scoring system combining multiple signals

Author: Nifty Trading System
Version: 1.0.0
"""


class OptionsAnalyzer:
    """
    Advanced options chain analyzer for Nifty 50 derivatives.
    
    Analyzes options data to generate conviction signals about market direction.
    Combines PCR, Max Pain, OI patterns, and ATM option metrics.
    
    Attributes:
        spot_price (float): Current Nifty spot price
        options_data (list): Raw options chain data
        calls (list): Filtered call options data
        puts (list): Filtered put options data
    """
    
    def __init__(self, spot_price, options_data):
        """
        Initialize the OptionsAnalyzer with spot price and options chain data.
        
        Args:
            spot_price (float): Current Nifty spot price
            options_data (list): List of option dictionaries with structure:
                {
                    'strike': int,
                    'type': str ('CE' for call, 'PE' for put),
                    'oi': int (open interest),
                    'volume': int (trading volume),
                    'ltp': float (last traded price),
                    'bid': float (bid price),
                    'ask': float (ask price),
                    'change_oi': int (change in OI from previous session)
                }
        
        Raises:
            None - gracefully handles empty data
        """
        self.spot_price = spot_price
        self.options_data = options_data if options_data else []
        self.calls = [o for o in self.options_data if o.get('type') == 'CE']
        self.puts = [o for o in self.options_data if o.get('type') == 'PE']
    
    def compute_pcr(self):
        """
        Compute Put-Call Ratio from open interest and volume.
        
        Returns:
            dict: {
                'oi_pcr': float - Put OI / Call OI ratio,
                'volume_pcr': float - Put Volume / Call Volume ratio,
                'interpretation': str - Sentiment interpretation
            }
        
        Interpretation guide:
            PCR > 1.3: BULLISH (contrarian - heavy put writing suggests support)
            PCR 1.0-1.3: MILDLY BULLISH
            PCR 0.8-1.0: NEUTRAL
            PCR < 0.8: BEARISH (contrarian - heavy call buying suggests resistance)
        """
        if not self.calls or not self.puts:
            return {
                'oi_pcr': 0.0,
                'volume_pcr': 0.0,
                'interpretation': 'INSUFFICIENT DATA'
            }
        
        total_call_oi = sum(c.get('oi', 0) for c in self.calls)
        total_put_oi = sum(p.get('oi', 0) for p in self.puts)
        
        total_call_volume = sum(c.get('volume', 0) for c in self.calls)
        total_put_volume = sum(p.get('volume', 0) for p in self.puts)
        
        oi_pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0.0
        volume_pcr = total_put_volume / total_call_volume if total_call_volume > 0 else 0.0
        
        # Interpret PCR using OI ratio
        if oi_pcr > 1.3:
            interpretation = "BULLISH (contrarian - heavy put writing suggests support)"
        elif oi_pcr > 1.0:
            interpretation = "MILDLY BULLISH"
        elif oi_pcr >= 0.8:
            interpretation = "NEUTRAL"
        else:
            interpretation = "BEARISH (contrarian - heavy call buying suggests resistance)"
        
        return {
            'oi_pcr': round(oi_pcr, 4),
            'volume_pcr': round(volume_pcr, 4),
            'interpretation': interpretation
        }
    
    def find_max_oi_levels(self):
        """
        Identify strikes with maximum open interest for calls and puts.
        
        These levels represent major support/resistance zones where option
        writers have concentrated positions.
        
        Returns:
            dict: {
                'max_call_oi_strike': int - Strike with highest call OI,
                'max_put_oi_strike': int - Strike with highest put OI,
                'max_call_oi': int - Highest call OI value,
                'max_put_oi': int - Highest put OI value
            }
        """
        result = {
            'max_call_oi_strike': None,
            'max_put_oi_strike': None,
            'max_call_oi': 0,
            'max_put_oi': 0
        }
        
        if not self.calls and not self.puts:
            return result
        
        if self.calls:
            max_call = max(self.calls, key=lambda x: x.get('oi', 0))
            result['max_call_oi_strike'] = max_call.get('strike')
            result['max_call_oi'] = max_call.get('oi', 0)
        
        if self.puts:
            max_put = max(self.puts, key=lambda x: x.get('oi', 0))
            result['max_put_oi_strike'] = max_put.get('strike')
            result['max_put_oi'] = max_put.get('oi', 0)
        
        return result
    
    def compute_max_pain(self):
        """
        Calculate Max Pain - the strike price at expiry where maximum options
        expire worthless, minimizing payout obligations for option sellers.
        
        The Max Pain principle assumes option writers manage positions to
        converge price toward a level maximizing profit. This represents
        institutional flow expectations.
        
        Algorithm:
            For each strike (potential expiry price):
                call_payout = sum of max(0, strike - K) * call_OI for each call strike K
                put_payout = sum of max(0, K - strike) * put_OI for each put strike K
                total_payout = call_payout + put_payout
            Max pain = strike with MINIMUM total_payout
        
        Returns:
            dict: {
                'max_pain_strike': int - Strike with maximum pain,
                'current_distance': float - Distance from spot to max pain,
                'direction_bias': str - BULLISH/BEARISH interpretation
            }
        """
        if not self.calls or not self.puts:
            return {
                'max_pain_strike': None,
                'current_distance': 0.0,
                'direction_bias': 'INSUFFICIENT DATA'
            }
        
        # Get all unique strikes
        all_strikes = set()
        for opt in self.calls + self.puts:
            all_strikes.add(opt.get('strike'))
        
        if not all_strikes:
            return {
                'max_pain_strike': None,
                'current_distance': 0.0,
                'direction_bias': 'INSUFFICIENT DATA'
            }
        
        min_pain = float('inf')
        max_pain_strike = None
        
        # Calculate payout for each possible expiry price
        for expiry_price in sorted(all_strikes):
            call_payout = 0
            for call in self.calls:
                strike = call.get('strike')
                oi = call.get('oi', 0)
                if expiry_price > strike:
                    call_payout += (expiry_price - strike) * oi
            
            put_payout = 0
            for put in self.puts:
                strike = put.get('strike')
                oi = put.get('oi', 0)
                if expiry_price < strike:
                    put_payout += (strike - expiry_price) * oi
            
            total_payout = call_payout + put_payout
            
            if total_payout < min_pain:
                min_pain = total_payout
                max_pain_strike = expiry_price
        
        current_distance = max_pain_strike - self.spot_price if max_pain_strike else 0
        
        if current_distance > 0:
            direction_bias = "BULLISH (price likely to drift up toward max pain)"
        elif current_distance < 0:
            direction_bias = "BEARISH (price likely to drift down toward max pain)"
        else:
            direction_bias = "NEUTRAL (spot near max pain)"
        
        return {
            'max_pain_strike': max_pain_strike,
            'current_distance': round(current_distance, 2),
            'direction_bias': direction_bias
        }
    
    def analyze_oi_buildup(self):
        """
        Identify strikes where new open interest is building.
        
        High positive change_oi at specific strikes indicates fresh positioning
        by institutions, suggesting trading conviction at those levels.
        
        Returns:
            dict: {
                'call_buildup_strikes': list of top 3 calls with highest change_oi,
                'put_buildup_strikes': list of top 3 puts with highest change_oi,
                'interpretation': str - Summary of OI buildup pattern
            }
        """
        result = {
            'call_buildup_strikes': [],
            'put_buildup_strikes': [],
            'interpretation': ''
        }
        
        if self.calls:
            sorted_calls = sorted(
                self.calls,
                key=lambda x: x.get('change_oi', 0),
                reverse=True
            )
            result['call_buildup_strikes'] = [
                {
                    'strike': c.get('strike'),
                    'change_oi': c.get('change_oi', 0),
                    'total_oi': c.get('oi', 0)
                }
                for c in sorted_calls[:3]
            ]
        
        if self.puts:
            sorted_puts = sorted(
                self.puts,
                key=lambda x: x.get('change_oi', 0),
                reverse=True
            )
            result['put_buildup_strikes'] = [
                {
                    'strike': p.get('strike'),
                    'change_oi': p.get('change_oi', 0),
                    'total_oi': p.get('oi', 0)
                }
                for p in sorted_puts[:3]
            ]
        
        # Interpret buildup pattern
        if result['call_buildup_strikes'] and result['put_buildup_strikes']:
            top_call_strike = result['call_buildup_strikes'][0]['strike']
            top_put_strike = result['put_buildup_strikes'][0]['strike']
            
            if top_call_strike and top_put_strike:
                if top_call_strike > self.spot_price and top_put_strike < self.spot_price:
                    result['interpretation'] = (
                        "NEUTRAL BUILDUP - Symmetric call and put buildup "
                        "at resistance and support"
                    )
                elif top_call_strike > self.spot_price:
                    result['interpretation'] = (
                        "CALL BUILDUP BIAS - Heavy call OI buildup at higher strikes "
                        "suggests resistance formation"
                    )
                elif top_put_strike < self.spot_price:
                    result['interpretation'] = (
                        "PUT BUILDUP BIAS - Heavy put OI buildup at lower strikes "
                        "suggests support formation"
                    )
        
        return result
    
    def find_atm_options(self):
        """
        Identify At-The-Money (ATM) options.
        
        ATM strike is rounded to the nearest 50 points from current spot price.
        ATM options have highest gamma and are most liquid for trading.
        
        Returns:
            dict: {
                'atm_strike': int - Nearest 50-point strike to spot,
                'atm_ce': dict or None - ATM call option data,
                'atm_pe': dict or None - ATM put option data
            }
        """
        # Round spot to nearest 50
        atm_strike = round(self.spot_price / 50) * 50
        
        atm_ce = None
        atm_pe = None
        
        for call in self.calls:
            if call.get('strike') == atm_strike:
                atm_ce = call
                break
        
        for put in self.puts:
            if put.get('strike') == atm_strike:
                atm_pe = put
                break
        
        return {
            'atm_strike': atm_strike,
            'atm_ce': atm_ce,
            'atm_pe': atm_pe
        }
    
    def get_options_score(self):
        """
        Generate integrated options analysis score combining all signals.
        
        Produces a composite sentiment score from -3 (strong bearish) to +3 (strong bullish).
        
        Scoring Components:
            PCR Analysis:
                PCR > 1.3: +1.0
                PCR > 1.0: +0.3
                PCR < 0.8: -1.0
                PCR < 1.0: -0.3
            
            Max Pain Direction:
                Max pain > spot: +0.5
                Max pain < spot: -0.5
            
            OI Buildup Patterns:
                Put buildup at/below spot: +0.5 (support building)
                Call buildup at/above spot: -0.5 (resistance building)
            
            Max OI Levels:
                Spot within 100 pts of max call OI: -0.5 (near resistance)
                Spot within 100 pts of max put OI: +0.5 (near support)
            
            Final score capped at -3.0 to +3.0
        
        Returns:
            dict: {
                'score': float - Integrated conviction score (-3 to +3),
                'direction': str - BULLISH/BEARISH/NEUTRAL classification,
                'pcr': dict - Put-Call Ratio analysis results,
                'support_level': int - Strike with max put OI,
                'resistance_level': int - Strike with max call OI,
                'max_pain': dict - Max pain calculation results,
                'oi_buildup': dict - OI buildup pattern analysis,
                'atm_options': dict - ATM option data,
                'signals': list of str - Detailed signal descriptions
            }
        """
        score = 0.0
        signals = []
        
        # Get all analyses
        pcr_data = self.compute_pcr()
        max_oi_data = self.find_max_oi_levels()
        max_pain_data = self.compute_max_pain()
        oi_buildup_data = self.analyze_oi_buildup()
        atm_data = self.find_atm_options()
        
        # PCR Scoring
        oi_pcr = pcr_data.get('oi_pcr', 0)
        if oi_pcr > 1.3:
            score += 1.0
            signals.append(f"Strong PCR {oi_pcr:.2f} - Heavy put writing suggests solid support")
        elif oi_pcr > 1.0:
            score += 0.3
            signals.append(f"Mild PCR {oi_pcr:.2f} - Slight put bias indicates support")
        elif oi_pcr < 0.8:
            score -= 1.0
            signals.append(f"Strong call bias PCR {oi_pcr:.2f} - Heavy call buying suggests resistance")
        elif oi_pcr < 1.0:
            score -= 0.3
            signals.append(f"Mild call bias PCR {oi_pcr:.2f} - Slight call lean indicates resistance")
        else:
            signals.append(f"Neutral PCR {oi_pcr:.2f}")
        
        # Max Pain Scoring
        max_pain_strike = max_pain_data.get('max_pain_strike')
        if max_pain_strike:
            if max_pain_strike > self.spot_price:
                score += 0.5
                signals.append(
                    f"Max pain {max_pain_strike} above spot - "
                    f"Institutional bias toward higher prices"
                )
            elif max_pain_strike < self.spot_price:
                score -= 0.5
                signals.append(
                    f"Max pain {max_pain_strike} below spot - "
                    f"Institutional bias toward lower prices"
                )
        
        # OI Buildup Scoring
        call_buildup = oi_buildup_data.get('call_buildup_strikes', [])
        put_buildup = oi_buildup_data.get('put_buildup_strikes', [])
        
        if put_buildup:
            put_strike = put_buildup[0].get('strike')
            if put_strike and put_strike <= self.spot_price:
                score += 0.5
                signals.append(
                    f"Put buildup at {put_strike} - Support formation in progress"
                )
        
        if call_buildup:
            call_strike = call_buildup[0].get('strike')
            if call_strike and call_strike >= self.spot_price:
                score -= 0.5
                signals.append(
                    f"Call buildup at {call_strike} - Resistance formation in progress"
                )
        
        # Max OI Level Scoring
        max_call_oi_strike = max_oi_data.get('max_call_oi_strike')
        max_put_oi_strike = max_oi_data.get('max_put_oi_strike')
        
        if max_call_oi_strike and abs(self.spot_price - max_call_oi_strike) <= 100:
            score -= 0.5
            signals.append(
                f"Spot within 100 pts of max call OI {max_call_oi_strike} - "
                f"Major resistance zone"
            )
        
        if max_put_oi_strike and abs(self.spot_price - max_put_oi_strike) <= 100:
            score += 0.5
            signals.append(
                f"Spot within 100 pts of max put OI {max_put_oi_strike} - "
                f"Major support zone"
            )
        
        # Cap score at -3.0 to +3.0
        score = max(-3.0, min(3.0, score))
        
        # Determine direction
        if score > 0.5:
            direction = "BULLISH"
        elif score < -0.5:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"
        
        return {
            'score': round(score, 2),
            'direction': direction,
            'pcr': pcr_data,
            'support_level': max_oi_data.get('max_put_oi_strike'),
            'resistance_level': max_oi_data.get('max_call_oi_strike'),
            'max_pain': max_pain_data,
            'oi_buildup': oi_buildup_data,
            'atm_options': atm_data,
            'signals': signals
        }
