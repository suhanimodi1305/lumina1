from datetime import datetime, timezone as dt_timezone


class TierSerializer:
    """Serialize/deserialize UserProfile tier state to/from a plain dict."""

    @staticmethod
    def serialize(profile) -> dict:
        expires = profile.subscription_expires_at
        return {
            'tier':                    profile.tier,
            'loyalty_points':          profile.loyalty_points,
            'referral_code':           profile.referral_code,
            'subscription_expires_at': expires.isoformat() if expires else None,
        }

    @staticmethod
    def deserialize(profile, data: dict):
        """Apply dict values back to profile (does not save)."""
        profile.tier           = data['tier']
        profile.loyalty_points = data['loyalty_points']
        profile.referral_code  = data['referral_code']
        expires_raw = data.get('subscription_expires_at')
        profile.subscription_expires_at = (
            datetime.fromisoformat(expires_raw).replace(tzinfo=dt_timezone.utc)
            if expires_raw else None
        )
        return profile
