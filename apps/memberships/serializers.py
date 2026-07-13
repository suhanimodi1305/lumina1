"""
TierSerializer — thin serializer for UserProfile tier data.

Spec reference: premium-membership-tiers Task 6
Requirements:  11.1, 11.2, 11.3
"""
from datetime import timezone as dt_tz
from datetime import datetime


class TierSerializer:
    """Serialize / deserialize UserProfile tier-related fields to/from a plain dict."""

    FIELDS = ('tier', 'loyalty_points', 'referral_code', 'subscription_expires_at')

    @staticmethod
    def serialize(profile) -> dict:
        """
        Convert a UserProfile instance to a dict.

        Returns:
            {
                "tier": str,
                "loyalty_points": int,
                "referral_code": str,
                "subscription_expires_at": ISO-8601 string | None
            }
        """
        expires = profile.subscription_expires_at
        return {
            'tier':                    profile.effective_tier,
            'loyalty_points':          profile.loyalty_points,
            'referral_code':           profile.referral_code,
            'subscription_expires_at': expires.isoformat() if expires is not None else None,
        }

    @staticmethod
    def deserialize(profile, data: dict):
        """
        Apply a serialized dict back onto a UserProfile instance.

        - Parses ISO-8601 datetime strings, attaches UTC timezone if naive.
        - Sets ``subscription_expires_at`` to None when the value is None/empty.
        - Does NOT call ``save()`` — the caller is responsible for persisting changes.

        Args:
            profile: UserProfile instance to mutate.
            data:    Dict produced by ``serialize()`` (or equivalent).

        Returns:
            The mutated profile instance (not yet saved).
        """
        if 'tier' in data:
            profile.tier = data['tier']

        if 'loyalty_points' in data:
            profile.loyalty_points = int(data['loyalty_points'])

        if 'referral_code' in data:
            profile.referral_code = data['referral_code']

        if 'subscription_expires_at' in data:
            raw = data['subscription_expires_at']
            if raw is None or raw == '':
                profile.subscription_expires_at = None
            else:
                dt = datetime.fromisoformat(raw)
                # Attach UTC if the parsed datetime has no tzinfo
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=dt_tz.utc)
                profile.subscription_expires_at = dt

        return profile
