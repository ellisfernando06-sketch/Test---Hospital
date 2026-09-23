
# ── UI Tienda ────────────────────────────────────────────────────────────

class CategoriaSelect(ui.Select):
    def __init__(self):
        opts = []
        for cid, meta in sorted(CATEGORIAS_META.items(), key=lambda x: x[1].get("orden", 99)):
            opts.append(discord.SelectOption(
                label=meta["nombre"][:100], value=cid,
                emoji=meta.get("emoji") or "🛒",
                description=f"Ver {meta['nombre']}"[:100],
            ))
        super().__init__(placeholder="🛒 Elige una categoría…", options=opts,
                         min_values=1, max_values=1, custom_id="tienda_cat")

    async def callback(self, inter: discord.Interaction):
        cat = self.values[0]
        items = items_por_categoria(cat)
        if not items:
            await inter.response.send_message("No hay productos.", ephemeral=True)
            return
        meta = CATEGORIAS_META.get(cat, {})
        emb = discord.Embed(
            title=f"{meta.get('emoji','🛒')} {meta.get('nombre', cat)}",
            description="Selecciona un producto (1 unidad).",
            color=0x2ECC71,
        )
        for iid, d in items[:15]:
            st = d.get("stock", -1)
            st_txt = "∞" if st < 0 else str(st)
            emb.add_field(
                name=f"{d.get('emoji','')} {d['nombre']} — {MONEDA}{d['precio']:.2f}",
                value=f"{d.get('desc','—')}\nStock: **{st_txt}**",
                inline=False,
            )
        await inter.response.send_message(embed=emb, view=ProductoView(cat), ephemeral=True)


class ProductoSelect(ui.Select):
    def __init__(self, cat: str):
        self.cat = cat
        opts = []
        for iid, d in items_por_categoria(cat)[:25]:
            opts.append(discord.SelectOption(
                label=f"{d['nombre'][:80]} ({MONEDA}{d['precio']:.0f})",
                value=iid, emoji=d.get("emoji") or "🛒",
                description=(d.get("desc") or "")[:100],
            ))
        super().__init__(placeholder="Elegir producto…", options=opts, min_values=1, max_values=1)

    async def callback(self, inter: discord.Interaction):
        ok, msg = comprar(inter.user.id, self.values[0], 1)
        bal = economia.obtener_balance(inter.user.id)
        emb = discord.Embed(
            title="🛒 Compra" if ok else "❌ Compra fallida",
            description=msg, color=0x2ECC71 if ok else 0xE74C3C,
        )
        emb.set_footer(text=f"Saldo: {MONEDA}{bal:.2f}")
        await inter.response.send_message(embed=emb, ephemeral=True)


class ProductoView(ui.View):
    def __init__(self, cat: str):
        super().__init__(timeout=120)
        self.add_item(ProductoSelect(cat))


class TiendaView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategoriaSelect())

    @ui.button(label="Mi saldo", style=discord.ButtonStyle.secondary, emoji="💰", custom_id="tienda_saldo")
    async def saldo(self, inter: discord.Interaction, btn: ui.Button):
        bal = economia.obtener_balance(inter.user.id)
        await inter.response.send_message(f"💰 Tu saldo: **{MONEDA}{bal:.2f}**", ephemeral=True)

    @ui.button(label="Mi inventario", style=discord.ButtonStyle.primary, emoji="🎒", custom_id="tienda_inv")
    async def inv(self, inter: discord.Interaction, btn: ui.Button):
        bag = inv_jugador(inter.user.id)
        if not bag:
            await inter.response.send_message("🎒 Inventario vacío.", ephemeral=True)
            return
        lines = [f"• {CATALOGO.get(i, {}).get('emoji','📦')} **{CATALOGO.get(i, {}).get('nombre', i)}** ×{c}" for i, c in bag.items()]
        await inter.response.send_message(
            embed=discord.Embed(title="🎒 Tu inventario", description="\n".join(lines), color=0x3498DB),
            ephemeral=True,
        )


def embed_tienda() -> discord.Embed:
    cats = "\n".join(
        f"{m.get('emoji','')} **{m['nombre']}**"
        for _, m in sorted(CATEGORIAS_META.items(), key=lambda x: x[1].get("orden", 99))
    )
    return discord.Embed(
        title="🛒 Tienda del Hospital",
        description=(
            "Compra con el saldo de tu cuenta hospitalaria.\n\n"
            f"**Categorías**\n{cats}\n\n"
            "Elige categoría en el menú. **Mi saldo** / **Mi inventario** abajo."
        ),
        color=0x27AE60,
    )


def registrar(bot: commands.Bot) -> None:
    @bot.tree.command(name="tienda", description="Abre la tienda del hospital")
    async def tienda_cmd(inter: discord.Interaction):
        await inter.response.send_message(embed=embed_tienda(), view=TiendaView(), ephemeral=True)

    @bot.tree.command(name="panel_tienda", description="Publica el panel permanente de la tienda")
    @app_commands.describe(canal="Canal donde publicar")
    async def panel_tienda(inter: discord.Interaction, canal: Optional[discord.TextChannel] = None):
        if not isinstance(inter.user, discord.Member) or not permisos.member_tiene_alguna_key(
            inter.user, "OWNER", "CO_OWNER", "DIRECTOR", "DIRECTOR_FINANCIERO", "DIRECTOR_ADMINISTRATIVO"
        ):
            await inter.response.send_message("❌ Sin permiso.", ephemeral=True)
            return
        dest = canal or inter.channel
        if not isinstance(dest, discord.TextChannel):
            await inter.response.send_message("❌ Canal inválido.", ephemeral=True)
            return
        await dest.send(embed=embed_tienda(), view=TiendaView())
        await inter.response.send_message(f"✅ Tienda en {dest.mention}", ephemeral=True)

    @bot.tree.command(name="mi_inventario", description="Ver tu inventario de la tienda")
    async def mi_inventario(inter: discord.Interaction):
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

    @bot.tree.command(name="bienvenida", description="Reclama el kit médico gratis (una vez)")
    async def bienvenida_cmd(inter: discord.Interaction):
        ok, msg = reclamar_bienvenida(inter.user.id)
        await inter.response.send_message(
            embed=discord.Embed(
                title="🎁 Bienvenida" if ok else "🎁 Bienvenida",
                description=msg, color=0x2ECC71 if ok else 0xF39C12,
            ),
            ephemeral=True,
        )

    bot.add_view(TiendaView())
    print("[tienda] OK")
