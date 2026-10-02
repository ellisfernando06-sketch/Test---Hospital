# -*- coding: utf-8 -*-
"""
certificado_oficial_ui.py — Flujo Discord del certificado oficial.

REGLA: ningún nombre de persona en código ni plantilla.
Beneficiarios y firmantes solo por menús User Select del bot.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

try:
    import config
except Exception:
    config = None


def _hospital() -> str:
    return getattr(config, "NOMBRE_HOSPITAL", None) or "HOSPITAL GENERAL"


def _display(m: discord.abc.User) -> str:
    if isinstance(m, discord.Member):
        return m.display_name or m.name
    return getattr(m, "display_name", None) or getattr(m, "name", str(m.id))


def _puede(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    try:
        import permisos

        return permisos.member_tiene_alguna_key(
            member,
            "DIR_DOCENCIA",
            "DIRECTOR_DOCENCIA",
            "FUNDADOR_OWNER",
            "CO_OWNER",
            "OWNER",
            "CANCILLER",
            "DIR_GENERAL",
            "DIRECTOR_GENERAL",
        )
    except Exception:
        return False


def _codigo_auto(guild_id: int) -> str:
    # HG-AAAA-#### secuencial simple por timestamp
    n = int(datetime.utcnow().timestamp()) % 10000
    return f"HG-{datetime.utcnow().year}-{n:04d}"


class DatosModal(ui.Modal, title="Datos del certificado"):
    departamento = ui.TextInput(
        label="Departamento / Ala",
        placeholder="Área o ala (texto libre)",
        max_length=80,
        required=False,
    )
    cargo = ui.TextInput(
        label="Cargo / Rango",
        placeholder="Cargo o rango del reconocimiento",
        max_length=80,
        required=False,
    )
    motivo = ui.TextInput(
        label="Motivo del reconocimiento",
        style=discord.TextStyle.paragraph,
        placeholder="Motivo institucional",
        max_length=200,
        required=True,
    )

    def __init__(self, parent: "CertificadoBuilderView"):
        super().__init__()
        self.parent = parent

    async def on_submit(self, interaction: discord.Interaction):
        self.parent.departamento = str(self.departamento).strip()
        self.parent.cargo = str(self.cargo).strip()
        self.parent.motivo = str(self.motivo).strip()
        await interaction.response.send_message(
            "✅ Datos guardados. Pulsa **Generar certificado** cuando las personas estén seleccionadas.",
            ephemeral=True,
        )


class CertificadoBuilderView(ui.View):
    """Menús de selección: beneficiarios + 3 autoridades. Sin nombres en código."""

    def __init__(self, author_id: int):
        super().__init__(timeout=900)
        self.author_id = author_id
        self.beneficiarios: List[discord.Member] = []
        self.director_docencia: Optional[discord.Member] = None
        self.director_departamento: Optional[discord.Member] = None
        self.encargado: Optional[discord.Member] = None
        self.departamento = ""
        self.cargo = ""
        self.motivo = ""

        # User selects
        self.sel_ben = ui.UserSelect(
            placeholder="Beneficiarios del certificado (uno o varios)",
            min_values=1,
            max_values=10,
            custom_id="cert_ben",
            row=0,
        )
        self.sel_ben.callback = self._on_ben
        self.add_item(self.sel_ben)

        self.sel_doc = ui.UserSelect(
            placeholder="Director de Docencia (firmante)",
            min_values=0,
            max_values=1,
            custom_id="cert_doc",
            row=1,
        )
        self.sel_doc.callback = self._on_doc
        self.add_item(self.sel_doc)

        self.sel_dep = ui.UserSelect(
            placeholder="Director del Ala / Departamento (firmante)",
            min_values=0,
            max_values=1,
            custom_id="cert_dep",
            row=2,
        )
        self.sel_dep.callback = self._on_dep
        self.add_item(self.sel_dep)

        self.sel_enc = ui.UserSelect(
            placeholder="Encargado de Otorgamiento de Certificados",
            min_values=0,
            max_values=1,
            custom_id="cert_enc",
            row=3,
        )
        self.sel_enc.callback = self._on_enc
        self.add_item(self.sel_enc)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Solo quien inició el comando puede usar este panel.", ephemeral=True
            )
            return False
        return True

    async def _on_ben(self, interaction: discord.Interaction):
        self.beneficiarios = [
            u for u in self.sel_ben.values if isinstance(u, discord.Member) and not u.bot
        ]
        n = len(self.beneficiarios)
        await interaction.response.send_message(
            f"✅ Beneficiarios seleccionados: **{n}**", ephemeral=True
        )

    async def _on_doc(self, interaction: discord.Interaction):
        vals = [u for u in self.sel_doc.values if isinstance(u, discord.Member)]
        self.director_docencia = vals[0] if vals else None
        await interaction.response.send_message(
            "✅ Director de Docencia seleccionado." if self.director_docencia else "—",
            ephemeral=True,
        )

    async def _on_dep(self, interaction: discord.Interaction):
        vals = [u for u in self.sel_dep.values if isinstance(u, discord.Member)]
        self.director_departamento = vals[0] if vals else None
        await interaction.response.send_message(
            "✅ Director del Ala / Departamento seleccionado."
            if self.director_departamento
            else "—",
            ephemeral=True,
        )

    async def _on_enc(self, interaction: discord.Interaction):
        vals = [u for u in self.sel_enc.values if isinstance(u, discord.Member)]
        self.encargado = vals[0] if vals else None
        await interaction.response.send_message(
            "✅ Encargado de otorgamiento seleccionado." if self.encargado else "—",
            ephemeral=True,
        )

    @ui.button(label="Completar datos del certificado", style=discord.ButtonStyle.primary, row=4)
    async def btn_datos(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DatosModal(self))

    @ui.button(label="Generar certificado", style=discord.ButtonStyle.success, row=4)
    async def btn_gen(self, interaction: discord.Interaction, button: ui.Button):
        if not self.beneficiarios:
            return await interaction.response.send_message(
                "❌ Selecciona al menos un **beneficiario** en el menú.", ephemeral=True
            )
        if not (self.motivo or "").strip():
            return await interaction.response.send_message(
                "❌ Completa los **datos** (motivo) con el botón correspondiente.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        from certificado_oficial_gen import generar_certificado_oficial

        codigo = _codigo_auto(interaction.guild.id if interaction.guild else 0)
        fecha = datetime.utcnow().strftime("%d / %m / %Y")

        names = [_display(m) for m in self.beneficiarios]
        buf = generar_certificado_oficial(
            beneficiarios=names,
            director_docencia=_display(self.director_docencia) if self.director_docencia else "",
            director_departamento=_display(self.director_departamento)
            if self.director_departamento
            else "",
            encargado_certificados=_display(self.encargado) if self.encargado else "",
            departamento=self.departamento,
            cargo=self.cargo,
            motivo=self.motivo,
            codigo_certificado=codigo,
            fecha_expedicion=fecha,
            hospital=_hospital(),
        )

        file = discord.File(buf, filename=f"certificado_{codigo.replace('-', '_')}.png")
        emb = discord.Embed(
            title="📜 Certificado oficial generado",
            description=(
                f"**Código:** `{codigo}`\n"
                f"**Beneficiarios:** {len(names)}\n"
                f"**Fecha:** {fecha}"
            ),
            color=0x1A2A52,
            timestamp=discord.utils.utcnow(),
        )
        await interaction.followup.send(embed=emb, file=file, ephemeral=True)

        # Intentar otorgar rol de certificado si el motivo/cargo mapea
        try:
            import cert_roles

            for m in self.beneficiarios:
                clave = cert_roles.resolver_clave_cert(self.motivo) or cert_roles.resolver_clave_cert(
                    self.cargo
                )
                if clave:
                    await cert_roles.otorgar_rol_certificado(
                        m, clave, reason=f"Certificado oficial {codigo}"
                    )
        except Exception:
            pass

        # Copia pública opcional en el canal
        try:
            buf2 = generar_certificado_oficial(
                beneficiarios=names,
                director_docencia=_display(self.director_docencia) if self.director_docencia else "",
                director_departamento=_display(self.director_departamento)
                if self.director_departamento
                else "",
                encargado_certificados=_display(self.encargado) if self.encargado else "",
                departamento=self.departamento,
                cargo=self.cargo,
                motivo=self.motivo,
                codigo_certificado=codigo,
                fecha_expedicion=fecha,
                hospital=_hospital(),
            )
            if interaction.channel and isinstance(
                interaction.channel, discord.TextChannel
            ):
                mentions = ", ".join(m.mention for m in self.beneficiarios)
                await interaction.channel.send(
                    content=f"🎓 Certificado oficial **`{codigo}`** · {mentions}",
                    file=discord.File(
                        buf2, filename=f"certificado_{codigo.replace('-', '_')}.png"
                    ),
                )
        except Exception:
            pass


def registrar(bot: commands.Bot) -> None:
    for name in ("certificado_oficial",):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(
        name="certificado_oficial",
        description="[Docencia] Certificado oficial editable — beneficiarios y firmas por menú",
    )
    async def certificado_oficial_cmd(inter: discord.Interaction):
        if not inter.guild or not isinstance(inter.user, discord.Member):
            return await inter.response.send_message(
                "❌ Solo en el servidor.", ephemeral=True
            )
        if not _puede(inter.user):
            return await inter.response.send_message(
                "❌ Solo Docencia / dirección.", ephemeral=True
            )

        view = CertificadoBuilderView(inter.user.id)
        emb = discord.Embed(
            title="📜 Certificado oficial de reconocimiento",
            description=(
                "**Plantilla institucional Hospital General**\n\n"
                "1. Selecciona **beneficiarios** (menú)\n"
                "2. Selecciona **Director de Docencia**\n"
                "3. Selecciona **Director del Ala / Departamento**\n"
                "4. Selecciona **Encargado de Otorgamiento**\n"
                "5. **Completar datos** (departamento, cargo, motivo)\n"
                "6. **Generar certificado**\n\n"
                "_Los nombres solo salen de las selecciones. "
                "Código y fecha se generan solos._"
            ),
            color=0x1A2A52,
        )
        await inter.response.send_message(embed=emb, view=view, ephemeral=True)

    print("[certificado_oficial_ui] OK — /certificado_oficial")
