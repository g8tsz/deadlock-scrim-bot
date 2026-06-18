import nextcord
from Tasks import getConfigData


def is_admin(interaction: nextcord.Interaction) -> bool:
    return interaction.user.guild_permissions.administrator


def is_staff(interaction: nextcord.Interaction) -> bool:
    if is_admin(interaction):
        return True
    config = getConfigData(interaction.guild.id)
    staff_role_id = config.get("staffRole")
    if not staff_role_id:
        return False
    role = interaction.guild.get_role(int(staff_role_id))
    return role is not None and role in interaction.user.roles
