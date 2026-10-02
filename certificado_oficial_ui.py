# -*- coding: utf-8 -*-
"""
certificado_oficial_ui.py — Certificado oficial enlazado a roles CERTIFICADOS y docencia.

- Beneficiarios y firmantes: solo menús User Select (sin nombres en código).
- Tipo de certificado: menú de roles CERTIFICADOS del organigrama.
- Al generar: otorga el rol + registra en docencia si está disponible.
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


def _codigo_auto() -> str:
    n = int(datetime.utcnow().timestamp()) % 10000
    return f"HG-{datetime.utcnow().year}-{n:04d}"


def _opciones_certificados() -> List[discord.SelectOption]:
    opts: List[discord.SelectOption] = []
    try:
        import roles_config

        for clave, (nombre, _col) in (getattr(roles_config, "CERTIFICADOS", {}) or {}).items():
            label = nombre if len(nombre) <= 100 else nombre[:97] + "…"
            opts.append(discord.SelectOption(label=label, value=clave, description=clave[:50]))
    except Exception:
        pass
    if not opts:
        opts.append(
            discord.SelectOption(
                label="Certificado genérico",
                value="_generico",
                description="Sin rol de organigrama",
            )
        )
    return opts[:25]


class DatosModal(ui.Modal, title="Datos del certificado"):
    departamento = ui.TextInput(
        label="Departamento / Ala",
        placeholder="Área o ala",
        max_length=80,
        required=False,
    )
    cargo = ui.TextInput(
        label="Cargo / Rango",
        placeholder="Cargo o rango",
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
            "✅ Datos guardados. Pulsa **Generar certificado**.",
            ephemeral=True,
        )


class CertificadoBuilderView(ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=900)
        self.author_id = author_id
        self.beneficiarios: List[discord.Member] = []
        self.director_docencia: Optional[discord.Member] = None
        self.director_departamento: Optional[discord.Member] = None
        self.encargado: Optional[discord.Member] = None
        self.clave_cert: Optional[str] = None
        self.nombre_cert: str = ""
        self.departamento = ""
        self.cargo = ""
        self.motivo = ""

        self.sel_cert = ui.Select(
            placeholder="Tipo de certificado (rol del organigrama)",
            min_values=1,
            max_values=1,
            options=_opciones_certificados(),
            custom_id="cert_tipo",
            row=0,
        )
        self.sel_cert.callback = self._on_cert
        self.add_item(self.sel_cert)

        self.sel_ben = ui.UserSelect(
            placeholder="Beneficiarios (uno o varios)",
            min_values=1,
            max_values=10,
            custom_id="cert_ben",
            row=1,
        )
        self.sel_ben.callback = self._on_ben
        self.add_item(self.sel_ben)

        self.sel_doc = ui.UserSelect(
            placeholder="Director de Docencia",
            min_values=0,
            max_values=1,
            custom_id="cert_doc",
            row=2,
        )
        self.sel_doc.callback = self._on_doc
        self.add_item(self.sel_doc)

        self.sel_dep = ui.UserSelect(
            placeholder="Director del Ala / Departamento",
            min_values=0,
            max_values=1,
            custom_id="cert_dep",
            row=3,
        )
        self.sel_dep.callback = self._on_dep
        self.add_item(self.sel_dep)

        # Encargado en row 4 con botones no cabe — usar segundo view step
        # Discord: max 5 rows. Rows 0-3 used. Row 4 = botones.
        # Encargado se elige en modal de datos extra o en select que reemplazamos:
        # Movemos encargado a un select que se muestra tras el tipo... 
        # Solución: row 4 tiene botones; encargado se pide en un UserSelect
        # sustituyendo temporalmente — mejor segundo panel al generar check.

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Solo quien inició el comando.", ephemeral=True
            )
            return False
        return True

    async def _on_cert(self, interaction: discord.Interaction):
        self.clave_cert = self.sel_cert.values[0]
        label = next(
            (o.label for o in self.sel_cert.options if o.value == self.clave_cert),
            self.clave_cert,
        )
        self.nombre_cert = label
        if self.clave_cert == "_generico":
            self.clave_cert = None
        await interaction.response.send_message(
            f"✅ Tipo de certificado: **{label}**\n"
            f"Al generar se otorgará el **rol** de este certificado.",
            ephemeral=True,
        )

    async def _on_ben(self, interaction: discord.Interaction):
        self.beneficiarios = [
            u for u in self.sel_ben.values if isinstance(u, discord.Member) and not u.bot
        ]
        await interaction.response.send_message(
            f"✅ Beneficiarios: **{len(self.beneficiarios)}**",
            ephemeral=True,
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
            "✅ Director del Ala seleccionado." if self.director_departamento else "—",
            ephemeral=True,
        )

    @ui.button(
        label="Encargado de otorgamiento",
        style=discord.ButtonStyle.secondary,
        row=4,
    )
    async def btn_enc(self, interaction: discord.Interaction, button: ui.Button):
        view = EncargadoPickView(self)
        await interaction.response.send_message(
            "Selecciona el **Encargado de Otorgamiento de Certificados**:",
            view=view,
            ephemeral=True,
        )

    @ui.button(label="Completar datos", style=discord.ButtonStyle.primary, row=4)
    async def btn_datos(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DatosModal(self))

    @ui.button(label="Generar certificado", style=discord.ButtonStyle.success, row=4)
    async def btn_gen(self, interaction: discord.Interaction, button: ui.Button):
        if not self.beneficiarios:
            return await interaction.response.send_message(
                "❌ Selecciona **beneficiarios**.", ephemeral=True
            )
        if not (self.motivo or "").strip():
            return await interaction.response.send_message(
                "❌ Completa los **datos** (motivo).", ephemeral=True
            )
        if not self.clave_cert and not self.nombre_cert:
            return await interaction.response.send_message(
                "❌ Selecciona el **tipo de certificado** (rol del organigrama).",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        from certificado_oficial_gen import generar_certificado_oficial

        codigo = _codigo_auto()
        fecha = datetime.utcnow().strftime("%d / %m / %Y")
        names = [_display(m) for m in self.beneficiarios]

        # Motivo en panel: si vacío de más detalle, usar nombre del cert
        motivo_final = self.motivo
        if self.nombre_cert and self.nombre_cert not in motivo_final:
            motivo_panel = self.nombre_cert
        else:
            motivo_panel = motivo_final

        buf = generar_certificado_oficial(
            beneficiarios=names,
            director_docencia=_display(self.director_docencia) if self.director_docencia else "",
            director_departamento=_display(self.director_departamento)
            if self.director_departamento
            else "",
            encargado_certificados=_display(self.encargado) if self.encargado else "",
            departamento=self.departamento,
            cargo=self.cargo or self.nombre_cert,
            motivo=motivo_panel,
            codigo_certificado=codigo,
            fecha_expedicion=fecha,
            hospital=_hospital(),
        )

        # ── Otorgar roles CERTIFICADOS ──
        roles_msg = []
        if self.clave_cert:
            try:
                import cert_roles

                for m in self.beneficiarios:
                    ok, msg = await cert_roles.otorgar_rol_certificado(
                        m,
                        self.clave_cert,
                        reason=f"Certificado oficial {codigo}",
                    )
                    roles_msg.append(f"{m.mention}: {msg}")
            except Exception as e:
                roles_msg.append(f"Error roles: {e}")

        # ── Registrar en docencia / capacitaciones ──
        reg_msg = []
        titulo = self.nombre_cert or self.motivo or "Certificado oficial"
        for m in self.beneficiarios:
            try:
                import docencia

                if hasattr(docencia, "emitir"):
                    docencia.emitir(
                        m.id,
                        titulo,
                        self.clave_cert or "personalizado",
                        self.motivo,
                        interaction.user.id,
                        notas=f"oficial {codigo}",
                        departamento=self.departamento,
                    )
                    reg_msg.append(f"docencia ✓ {m.display_name}")
            except Exception:
                pass
            try:
                import capacitaciones

                capacitaciones.certificar(m.id, titulo, interaction.user.id)
                reg_msg.append(f"cap ✓ {m.display_name}")
            except Exception:
                pass

        file = discord.File(buf, filename=f"certificado_{codigo.replace('-', '_')}.png")
        emb = discord.Embed(
            title="📜 Certificado oficial generado",
            description=(
                f"**Código:** `{codigo}`\n"
                f"**Tipo / rol:** {self.nombre_cert or '—'}\n"
                f"**Clave:** `{self.clave_cert or '—'}`\n"
                f"**Beneficiarios:** {len(names)}\n"
                f"**Fecha:** {fecha}\n\n"
                f"**Roles otorgados:**\n"
                + ("\n".join(roles_msg) if roles_msg else "_ninguno_")
                + "\n\n**Registro:**\n"
                + (", ".join(reg_msg) if reg_msg else "_sin módulo docencia_")
            ),
            color=0x1A2A52,
            timestamp=discord.utils.utcnow(),
        )
        await interaction.followup.send(embed=emb, file=file, ephemeral=True)

        try:
            buf2 = generar_certificado_oficial(
                beneficiarios=names,
                director_docencia=_display(self.director_docencia) if self.director_docencia else "",
                director_departamento=_display(self.director_departamento)
                if self.director_departamento
                else "",
                encargado_certificados=_display(self.encargado) if self.encargado else "",
                departamento=self.departamento,
                cargo=self.cargo or self.nombre_cert,
                motivo=motivo_panel,
                codigo_certificado=codigo,
                fecha_expedicion=fecha,
                hospital=_hospital(),
            )
            if interaction.channel and isinstance(interaction.channel, discord.TextChannel):
                mentions = ", ".join(m.mention for m in self.beneficiarios)
                await interaction.channel.send(
                    content=f"🎓 **`{codigo}`** · {self.nombre_cert or 'Certificado'} · {mentions}",
                    file=discord.File(
                        buf2, filename=f"certificado_{codigo.replace('-', '_')}.png"
                    ),
                )
        except Exception:
            pass


class EncargadoPickView(ui.View):
    def __init__(self, parent: CertificadoBuilderView):
        super().__init__(timeout=300)
        self.parent = parent
        sel = ui.UserSelect(
            placeholder="Encargado de Otorgamiento de Certificados",
            min_values=1,
            max_values=1,
        )
        sel.callback = self._picked
        self.add_item(sel)
        self.sel = sel

    async def _picked(self, interaction: discord.Interaction):
        vals = [u for u in self.sel.values if isinstance(u, discord.Member)]
        self.parent.encargado = vals[0] if vals else None
        await interaction.response.send_message(
            "✅ Encargado de otorgamiento seleccionado.", ephemeral=True
        )
        self.stop()


def registrar(bot: commands.Bot) -> None:
    for name in ("certificado_oficial",):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(
        name="certificado_oficial",
        description="[Docencia] Certificado oficial + rol CERTIFICADOS + registro",
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
                "**Enlazado al organigrama de certificados**\n\n"
                "1. **Tipo de certificado** → rol que se otorgará\n"
                "2. **Beneficiarios** (menú de miembros)\n"
                "3. **Director de Docencia**\n"
                "4. **Director del Ala / Departamento**\n"
                "5. **Encargado de otorgamiento**\n"
                "6. **Completar datos** (depto, cargo, motivo)\n"
                "7. **Generar** → imagen + rol + registro en docencia\n\n"
                "_Ningún nombre va en la plantilla hasta que elijas en los menús._"
            ),
            color=0x1A2A52,
        )
        await inter.response.send_message(embed=emb, view=view, ephemeral=True)

    print("[certificado_oficial_ui] OK — enlazado a CERTIFICADOS + docencia")
