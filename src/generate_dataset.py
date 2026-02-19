import argparse, random, math
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

def gen_dataset(n_athletes=120, days=120, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    start = datetime(2024,1,1)
    sports = ["running","football","basketball","cycling","hockey","badminton"]
    for a in range(n_athletes):
        athlete_id = f"A{a:04d}"
        sport = rng.choice(sports)
        # Athlete-specific baselines
        vo2max = rng.normal(50, 7)  # ml/kg/min
        bmr = rng.normal(1600, 150) + rng.normal(400,100)  # kcal/day
        sweat_rate_base = rng.uniform(0.6, 1.2)  # L/hr at 20C moderate activity
        body_mass = rng.normal(70, 8)  # kg
        # adherence tendency
        hydration_adherence = rng.uniform(0.6, 1.1)  # >1 means over-hydration tendency
        nutrition_adherence = rng.uniform(0.7, 1.1)

        dt = start
        fatigue_carry = 0.0
        for d in range(days):
            # Environment
            temp = float(rng.normal(24, 6))
            humidity = float(np.clip(rng.normal(0.55,0.15), 0.2, 0.95))
            session_mins = float(np.clip(rng.normal(60, 25), 20, 150))
            intensity = float(np.clip(rng.normal(0.6, 0.2), 0.2, 1.0))  # 0..1

            # Sleep & soreness
            sleep_hours = float(np.clip(rng.normal(7.2, 1.2), 3.5, 10.0))
            soreness = float(np.clip(rng.normal(3, 1.8) + fatigue_carry*0.8, 0, 10))

            # Sweat loss model (L)
            sweat_rate = sweat_rate_base * (1 + 0.03*(temp-20)) * (0.7 + 0.6*intensity)
            sweat_loss = sweat_rate * (session_mins/60.0)

            # Intake behaviors (stochastic around adherence)
            water_intake = float(np.clip(rng.normal(sweat_loss*hydration_adherence, 0.3), 0.1, 5.0))
            # Energy expenditure
            activity_cal = float(session_mins * (6 + 6*intensity))  # MET-ish scaled
            calories_in = float(np.clip(rng.normal((bmr+activity_cal)*nutrition_adherence, 250), 1000, 6000))

            # Derived
            hydration_deficit_pct = float(np.clip( (sweat_loss - water_intake) / max(sweat_loss,1e-6) * 100.0 , -30, 80))
            caloric_balance = float(calories_in - (bmr + activity_cal))

            # Fatigue index
            fatigue = (
                0.35*np.clip(hydration_deficit_pct, -10, 80)/80
                + 0.25*np.tanh(-caloric_balance/800)
                + 0.25*(1 - sleep_hours/10)
                + 0.15*soreness/10
            )
            fatigue = float(np.clip(fatigue*10, 0, 10))

            # Performance measures
            hr_rest = float(np.clip(60 - (vo2max-45)*0.6 + rng.normal(0,3) + fatigue*0.5, 42, 90))
            hr_avg = float(np.clip(110 + intensity*60 + rng.normal(0,5), 80, 200))
            distance = float(np.clip((session_mins/10)*(1.2+intensity*1.5)+rng.normal(0,0.6), 0.5, 30))
            pace = float(np.clip( (session_mins / max(distance,0.2)) , 2.5, 12.0))  # min/km

            # Update fatigue carry-over
            fatigue_carry = float(np.clip(fatigue_carry*0.6 + (fatigue-4)/10, 0, 6))

            rows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "athlete_id": athlete_id,
                "sport": sport,
                "vo2max": round(vo2max,2),
                "bmr": round(bmr,1),
                "body_mass": round(body_mass,1),
                "sleep_hours": round(sleep_hours,2),
                "soreness": round(soreness,2),
                "temp_c": round(temp,1),
                "humidity": round(humidity,3),
                "session_mins": round(session_mins,1),
                "intensity": round(intensity,3),
                "hr_rest": round(hr_rest,1),
                "hr_avg": round(hr_avg,1),
                "distance_km": round(distance,2),
                "pace_min_per_km": round(pace,2),
                "sweat_loss_L": round(sweat_loss,3),
                "water_intake_L": round(water_intake,3),
                "activity_calories": round(activity_cal,1),
                "calories_in": round(calories_in,1),
                "hydration_deficit_pct": round(hydration_deficit_pct,2),
                "caloric_balance": round(caloric_balance,1),
                "fatigue_score": round(fatigue,2),
            })
            dt += timedelta(days=1)
    return pd.DataFrame(rows)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=str, default="data/synthetic_logs.csv")
    ap.add_argument("--n_athletes", type=int, default=120)
    ap.add_argument("--days", type=int, default=120)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    df = gen_dataset(args.n_athletes, args.days, args.seed)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows to {args.out}")

if __name__ == "__main__":
    main()
