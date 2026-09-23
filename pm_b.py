
class PanelMiembrosView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Reglas (MD)", style=discord.ButtonStyle.primary, emoji="📜", custom_id="pm_reglas")
    async def reglas(self, inter: discord.Interaction, btn: ui.Button):
        if not isinstance(inter.user, discord.Member):
            await inter.response.send_message("Solo en el servidor.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)
        try:
            from comunidad import enviar_reglas_dm, ya_acepto
            if ya_acepto(inter.user.id):
                await inter.followup.send("Ya aceptaste las reglas. Usa `/reglas` para reenviar.", ephemeral=True)
                return
            ok, err = await enviar_reglas_dm(inter.user)
            if ok:
                await inter.followup.send(
                    "📬 Reglas en tus **MD**. Pulsa **Acepto las reglas** allí para el rol de comunidad.",
                    ephemeral=True,
                )
            else:
                await inter.followup.send(f"❌ {err}", ephemeral=True)
        except Exception as e:
            await inter.followup.send(f"❌ {e}", ephemeral=True)

    @ui.button(label="Bienvenida", style=discord.ButtonStyle.success, emoji="🎁", custom_id="pm_bienvenida")
    async def bienvenida(self, inter: discord.Interaction, btn: ui.Button):
        try:
            from tienda import reclamar_bienvenida
            ok, msg = reclamar_bienvenida(inter.user.id)
            await inter.response.send_message(
                embed=discord.Embed(
                    title="🎁 Kit de bienvenida", description=msg,
                    color=0x2ECC71 if ok else 0xF39C12,
                ),
                ephemeral=True,
            )
        except Exception as e:
            await inter.response.send_message(f"❌ {e}", ephemeral=True)

    @ui.button(label="Tienda", style=discord.ButtonStyle.primary, emoji="🛒", custom_id="pm_tienda")
    async def tienda_btn(self, inter: discord.Interaction, btn: ui.Button):
        try:
            from tienda import embed_tienda, TiendaView
            await inter.response.send_message(embed=embed_tienda(), view=TiendaView(), ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"❌ Tienda: {e}", ephemeral=True)

    @ui.button(label="Mi inventario", style=discord.ButtonStyle.secondary, emoji="🎒", custom_id="pm_inv")
    async def inv(self, inter: discord.Interaction, btn: ui.Button):
        try:
            from tienda import inv_jugador, CATALOGO
            bag = inv_jugador(inter.user.id)
            if not bag:
                await inter.response.send_message("🎒 Inventario vacío.", ephemeral=True)
                return
            lines = [
                f"• {CATALOGO.get(i, {}).get('emoji','📦')} **{CATALOGO.get(i, {}).get('nombre', i)}** ×{c}"
                for i, c in bag.items()
            ]
            await inter.response.send_message(
                embed=discord.Embed(title="🎒 Inventario", description="\n".join(lines), color=0x3498DB),
                ephemeral=True,
            )
        except Exception as e:
            await inter.response.send_message(f"❌ {e}", ephemeral=True)

    @ui.button(label="Mi expediente", style=discord.ButtonStyle.secondary, emoji="📁", custom_id="pm_exp")
    async def exp(self, inter: discord.Interaction, btn: ui.Button):
        await inter.response.send_message("Usa `/mi_expediente` o `/ficha`.", ephemeral=True)


def registrar(bot: commands.Bot) -> None:

    @bot.tree.command(name="panel_staff_disciplina",
                      description="Panel staff: sanciones/investigaciones")
    @app_commands.describe(canal="Canal del panel", canal_logs="Canal de evaluación")
    async def panel_staff_disciplina(inter: discord.Interaction,
                                     canal: discord.TextChannel,
                                     canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        emb = discord.Embed(
            title="⚖️ Panel Staff — Disciplina",
            description="Solo jefes/dirección. Sanción · investigación · apelación · reporte.",
            color=0x8E44AD)
        await _pub(inter, canal, canal_logs, "staff_disciplina", emb, PanelStaffDiscView(bot), "Panel Staff")
        logs_store.set_canal("log_sanciones", canal_logs.id)
        logs_store.set_canal("log_investigaciones", canal_logs.id)

    @bot.tree.command(name="panel_postulaciones", description="Panel postulaciones")
    @app_commands.describe(canal="Canal del panel", canal_logs="Canal de evaluación")
    async def panel_postulaciones(inter: discord.Interaction,
                                  canal: discord.TextChannel,
                                  canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        emb = discord.Embed(title="📋 Postulaciones", description="Elige departamento.", color=0x3498DB)
        await _pub(inter, canal, canal_logs, "log_postulaciones", emb, PanelPostView(), "Postulaciones")

    @bot.tree.command(name="panel_quejas", description="Panel quejas")
    @app_commands.describe(canal="Canal del panel", canal_logs="Canal RRHH")
    async def panel_quejas(inter: discord.Interaction,
                           canal: discord.TextChannel,
                           canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        emb = discord.Embed(title="📢 Quejas", description="Queja formal confidencial.", color=0xE67E22)
        await _pub(inter, canal, canal_logs, "log_quejas", emb, PanelQuejaView(), "Quejas")

    @bot.tree.command(name="panel_miembros", description="Panel pacientes/miembros")
    @app_commands.describe(canal="Canal del panel")
    async def panel_miembros(inter: discord.Interaction,
                             canal: Optional[discord.TextChannel] = None):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message("❌ Canal inválido.", ephemeral=True)
            return
        emb = discord.Embed(
            title="👤 Panel de Miembros",
            description=(
                "• **Reglas** → MD + rol comunidad\n"
                "• **Bienvenida** → kit médico gratis (1 vez)\n"
                "• **Tienda** / inventario\n"
                "• Expediente"
            ),
            color=0x1ABC9C,
        )
        await dest.send(embed=emb, view=PanelMiembrosView())
        await inter.response.send_message(f"✅ Panel miembros en {dest.mention}.", ephemeral=True)

    @bot.tree.command(name="panel_solicitudes_logs", description="Solicitudes + canal logs")
    @app_commands.describe(canal="Canal panel", canal_logs="Canal evaluación")
    async def panel_solicitudes_logs(inter: discord.Interaction,
                                     canal: discord.TextChannel,
                                     canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        logs_store.set_canal("log_solicitudes", canal_logs.id)
        emb = discord.Embed(title="📩 Solicitudes", description="Selecciona tipo de solicitud.", color=0x3498DB)
        view = PanelSolicitudesView(bot) if PanelSolicitudesView else ui.View()
        await canal.send(embed=emb, view=view)
        await inter.response.send_message(
            f"✅ Solicitudes en {canal.mention}\n📥 Logs → {canal_logs.mention}", ephemeral=True)

    @bot.tree.command(name="configurar_canal_logs", description="Asigna canal de logs")
    @app_commands.describe(tipo="Tipo", canal_logs="Canal")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Solicitudes", value="log_solicitudes"),
        app_commands.Choice(name="Postulaciones", value="log_postulaciones"),
        app_commands.Choice(name="Quejas", value="log_quejas"),
        app_commands.Choice(name="Sanciones", value="log_sanciones"),
        app_commands.Choice(name="Tickets", value="log_tickets"),
    ])
    async def configurar_canal_logs(inter: discord.Interaction,
                                    tipo: app_commands.Choice[str],
                                    canal_logs: discord.TextChannel):
        if not _puede_pub(inter.user):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        logs_store.set_canal(tipo.value, canal_logs.id)
        await inter.response.send_message(f"✅ `{tipo.value}` → {canal_logs.mention}", ephemeral=True)

    bot.add_view(PanelStaffDiscView(bot))
    bot.add_view(PanelPostView())
    bot.add_view(PanelQuejaView())
    bot.add_view(PanelMiembrosView())
    print("[paneles_miembros] OK")
