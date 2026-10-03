# -*- coding: utf-8 -*-
"""
certificado_oficial_ui.py — Flujo interno; firmas registradas en el diploma.
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
            opts.append(discord.SelectOption(label=label, value=clave))
    except Exception:
        pass
    if not opts:
        opts.append(discord.SelectOption(label="Certificado genérico", value="_generico"))
    return opts[:25]


def _ruta_firma(member: Optional[discord.Member]) -> Optional[str]:
    if not member:
        return None
    try:
        from certificado_oficial_gen import resolver_ruta_firma_usuario

        return resolver_ruta_firma_usuario(member.id)
    except Exception:
        try:
            import firmas

            info = firmas.obtener_firma_usuario(member.id)
            if info and info.get("file"):
                p = firmas.ruta_firma(info["file"])
                return p if p else None
        except Exception:
            return None
    return None


def _panel_embed(view: "CertificadoBuilderView") -> discord.Embed:
    ben = ", ".join(_display(m) for m in view.beneficiarios) if view.beneficiarios else "—"
    if len(ben) > 200:
        ben = ben[:197] + "…"

    def _firma_estado(m: Optional[discord.Member]) -> str:
        if not m:
            return "—"
        return f"{_display(m)} · {'✍️ firma OK' if _ruta_firma(m) else '⚠️ sin firma registrada'}"

    emb = discord.Embed(
        title="📜 Certificado oficial",
        description=(
            "Completa los menús y pulsa **Generar**.\n"
            "Las **firmas registradas** (`/registrar_firma`) se colocan **sobre cada raya**.\n"
            "_Proceso interno: sin avisos intermedios._"
        ),
        color=0x1A2A52,
    )
    emb.add_field(
        name="Estado",
        value=(
            f"**Tipo:** {view.nombre_cert or '—'}\n"
            f"**Beneficiarios:** {ben}\n"
            f"**Dir. Docencia:** {_firma_estado(view.director_docencia)}\n"
            f"**Dir. Ala:** {_firma_estado(view.director_departamento)}\n"
            f"**Encargado:** {_firma_estado(view.encargado)}\n"
            f"**Datos:** {'sí' if (view.motivo or '').strip() else 'pendiente'}"
        ),
        inline=False,
    )
    return emb


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
        try:
            await interaction.response.edit_message(
                embed=_panel_embed(self.parent), view=self.parent
            )
        except Exception:
            await interaction.response.defer()


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
        self.message: Optional[discord.Message] = None

        self.sel_cert = ui.Select(
            placeholder="Tipo de certificado",
            min_values=1,
            max_values=1,
            options=_opciones_certificados(),
            row=0,
        )
        self.sel_cert.callback = self._on_cert
        self.add_item(self.sel_cert)

        self.sel_ben = ui.UserSelect(
            placeholder="Beneficiarios",
            min_values=1,
            max_values=10,
            row=1,
        )
        self.sel_ben.callback = self._on_ben
        self.add_item(self.sel_ben)

        self.sel_doc = ui.UserSelect(
            placeholder="Director de Docencia",
            min_values=0,
            max_values=1,
            row=2,
        )
        self.sel_doc.callback = self._on_doc
        self.add_item(self.sel_doc)

        self.sel_dep = ui.UserSelect(
            placeholder="Director del Ala / Departamento",
            min_values=0,
            max_values=1,
            row=3,
        )
        self.sel_dep.callback = self._on_dep
        self.add_item(self.sel_dep)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Solo quien ejecutó el comando.", ephemeral=True
            )
            return False
        return True

    async def _refresh(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.edit_message(
                embed=_panel_embed(self), view=self
            )
        except discord.InteractionResponded:
            try:
                await interaction.edit_original_response(
                    embed=_panel_embed(self), view=self
                )
            except Exception:
                pass
        except Exception:
            try:
                await interaction.response.defer()
            except Exception:
                pass

    async def _on_cert(self, interaction: discord.Interaction):
        self.clave_cert = self.sel_cert.values[0]
        label = next(
            (o.label for o in self.sel_cert.options if o.value == self.clave_cert),
            self.clave_cert,
        )
        self.nombre_cert = label
        if self.clave_cert == "_generico":
            self.clave_cert = None
        await self._refresh(interaction)

    async def _on_ben(self, interaction: discord.Interaction):
        self.beneficiarios = [
            u for u in self.sel_ben.values if isinstance(u, discord.Member) and not u.bot
        ]
        await self._refresh(interaction)

    async def _on_doc(self, interaction: discord.Interaction):
        vals = [u for u in self.sel_doc.values if isinstance(u, discord.Member)]
        self.director_docencia = vals[0] if vals else None
        await self._refresh(interaction)

    async def _on_dep(self, interaction: discord.Interaction):
        vals = [u for u in self.sel_dep.values if isinstance(u, discord.Member)]
        self.director_departamento = vals[0] if vals else None
        await self._refresh(interaction)

    @ui.button(label="Encargado", style=discord.ButtonStyle.secondary, row=4)
    async def btn_enc(self, interaction: discord.Interaction, button: ui.Button):
        view = EncargadoPickView(self)
        await interaction.response.send_message(view=view, ephemeral=True)

    @ui.button(label="Datos", style=discord.ButtonStyle.primary, row=4)
    async def btn_datos(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DatosModal(self))

    @ui.button(label="Generar", style=discord.ButtonStyle.success, row=4)
    async def btn_gen(self, interaction: discord.Interaction, button: ui.Button):
        if not self.beneficiarios:
            return await interaction.response.send_message(
                "❌ Faltan beneficiarios.", ephemeral=True
            )
        if not (self.motivo or "").strip():
            return await interaction.response.send_message(
                "❌ Completa **Datos** (motivo).", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        try:
            from certificado_oficial_gen import generar_certificado_oficial
        except Exception as e:
            return await interaction.followup.send(
                f"❌ Error al cargar generador: {e}", ephemeral=True
            )

        codigo = _codigo_auto()
        fecha = datetime.utcnow().strftime("%d / %m / %Y")
        names = [_display(m) for m in self.beneficiarios]
        motivo_panel = self.motivo
        if self.nombre_cert and self.nombre_cert not in motivo_panel:
            motivo_panel = self.nombre_cert

        # Firmas registradas (imagen sobre cada raya)
        f_doc = _ruta_firma(self.director_docencia)
        f_dep = _ruta_firma(self.director_departamento)
        f_enc = _ruta_firma(self.encargado)

        avisos = []
        if self.director_docencia and not f_doc:
            avisos.append("Dir. Docencia sin `/registrar_firma`")
        if self.director_departamento and not f_dep:
            avisos.append("Dir. Ala sin `/registrar_firma`")
        if self.encargado and not f_enc:
            avisos.append("Encargado sin `/registrar_firma`")

        try:
            buf = generar_certificado_oficial(
                beneficiarios=names,
                director_docencia=_display(self.director_docencia)
                if self.director_docencia
                else "",
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
                firma_docencia=f_doc,
                firma_departamento=f_dep,
                firma_encargado=f_enc,
            )
        except Exception as e:
            return await interaction.followup.send(
                f"❌ Error al generar imagen: {e}", ephemeral=True
            )

        if self.clave_cert:
            try:
                import cert_roles

                for m in self.beneficiarios:
                    await cert_roles.otorgar_rol_certificado(
                        m, self.clave_cert, reason=f"Certificado oficial {codigo}"
                    )
            except Exception:
                pass

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
            except Exception:
                pass
            try:
                import capacitaciones

                capacitaciones.certificar(m.id, titulo, interaction.user.id)
            except Exception:
                pass

        file = discord.File(buf, filename=f"certificado_{codigo.replace('-', '_')}.png")
        desc = f"`{codigo}` · {fecha}"
        if avisos:
            desc += "\n⚠️ " + " · ".join(avisos)
        emb = discord.Embed(
            title="📜 Certificado generado",
            description=desc,
            color=0x1A2A52,
        )
        await interaction.followup.send(embed=emb, file=file, ephemeral=True)

        try:
            if interaction.message:
                await interaction.message.edit(
                    content="✅ Listo.", embed=None, view=None
                )
        except Exception:
            pass


class EncargadoPickView(ui.View):
    def __init__(self, parent: CertificadoBuilderView):
        super().__init__(timeout=300)
        self.parent = parent
        sel = ui.UserSelect(
            placeholder="Encargado de otorgamiento",
            min_values=1,
            max_values=1,
        )
        sel.callback = self._picked
        self.add_item(sel)
        self.sel = sel

    async def _picked(self, interaction: discord.Interaction):
        vals = [u for u in self.sel.values if isinstance(u, discord.Member)]
        self.parent.encargado = vals[0] if vals else None
        try:
            await interaction.response.edit_message(content="✅", view=None)
        except Exception:
            try:
                await interaction.response.defer()
            except Exception:
                pass
        try:
            if self.parent.message:
                await self.parent.message.edit(
                    embed=_panel_embed(self.parent), view=self.parent
                )
        except Exception:
            pass
        self.stop()


def registrar(bot: commands.Bot) -> None:
    for name in ("certificado_oficial",):
        try:
            bot.tree.remove_command(name)
        except Exception:
            pass

    @bot.tree.command(
        name="certificado_oficial",
        description="[Docencia] Certificado oficial (firmas sobre las rayas)",
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
        await inter.response.send_message(
            embed=_panel_embed(view), view=view, ephemeral=True
        )
        try:
            view.message = await inter.original_response()
        except Exception:
            view.message = None

    print("[certificado_oficial_ui] OK — firmas registradas sobre las rayas")
