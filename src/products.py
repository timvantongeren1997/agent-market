from scipy import stats


class Underlying:
    def __init__(self, base_price: float) -> None:
        self.price = base_price

        # Random walk parameters
        self.mu = 0
        self.sigma = 0.25

    def simulate_one_step(self):
        self.price += float(stats.norm.rvs(loc=self.mu, scale=self.sigma, size=1))
