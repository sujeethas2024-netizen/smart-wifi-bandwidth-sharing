from .utility import calculate_utility


# ==================================================
# ACTIVITY WEIGHTS
# ==================================================
#
# Different activities have different bandwidth
# requirements / importance.
#
# Higher weight = higher benefit from bandwidth.
# ==================================================

ACTIVITY_WEIGHTS = {

    "browsing": 1.0,

    "online_class": 1.5,

    "gaming": 1.3,

    "streaming": 1.4,

    "downloading": 1.1

}


# ==================================================
# USER / PLAYER
# ==================================================

class User:

    def __init__(
        self,
        user_id,
        activity,
        requested_bandwidth
    ):
        """
        Represents one Wi-Fi user/player.

        In Game Theory:

            User = Player

            requested_bandwidth = Maximum desired strategy

            allocated_bandwidth = Actual strategy
        """

        self.user_id = user_id

        self.activity = activity

        self.requested_bandwidth = float(
            requested_bandwidth
        )

        # Get activity importance
        self.weight = ACTIVITY_WEIGHTS.get(
            activity,
            1.0
        )

        # Initially no bandwidth is allocated
        self.allocated_bandwidth = 0.0

        # Initially utility is zero
        self.utility = 0.0


    def calculate_utility(
        self,
        total_usage,
        total_bandwidth,
        congestion_penalty=0.5
    ):
        """
        Calculate this user's utility.
        """

        self.utility = calculate_utility(

            bandwidth=self.allocated_bandwidth,

            total_usage=total_usage,

            total_bandwidth=total_bandwidth,

            activity_weight=self.weight,

            congestion_penalty=congestion_penalty
        )

        return self.utility


# ==================================================
# CONGESTION GAME
# ==================================================

class CongestionGame:

    def __init__(
        self,
        total_bandwidth,
        users,
        congestion_penalty=0.5
    ):
        """
        Represents the complete Wi-Fi congestion game.
        """

        self.total_bandwidth = float(
            total_bandwidth
        )

        self.users = users

        self.congestion_penalty = (
            congestion_penalty
        )


    # ==================================================
    # TOTAL BANDWIDTH USED
    # ==================================================

    def total_usage(self):

        return sum(

            user.allocated_bandwidth

            for user in self.users

        )


    # ==================================================
    # CALCULATE ALL USER UTILITIES
    # ==================================================

    def calculate_utilities(self):

        usage = self.total_usage()

        for user in self.users:

            user.calculate_utility(

                total_usage=usage,

                total_bandwidth=
                    self.total_bandwidth,

                congestion_penalty=
                    self.congestion_penalty

            )


    # ==================================================
    # GET CURRENT STATE
    # ==================================================

    def get_state(self):

        return {

            user.user_id:
                user.allocated_bandwidth

            for user in self.users

        }


    # ==================================================
    # GET CURRENT UTILITIES
    # ==================================================

    def get_utilities(self):

        return {

            user.user_id:
                user.utility

            for user in self.users

        }