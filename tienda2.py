
# ── UI Tienda (panel público con precios por categoría) ─────────────────

class CategoriaSelect(ui.Select):
    def __init__(self):
        opts = []
        for cid, meta in sorted(CATEGORIAS_META.items(), key=lambda x: x[1].get("orden", 99)):
            items = items_por_categoria(cid)
            n = len(items)
            precios = [d["precio"] for _, d in items] if items else [0]
            rango = f"{MONEDA}{min(precios):.0f}–{MONEDA}{max(precios):.0f}" if items else "—"
            opts.append(discord.SelectOption(
                label=meta["nombre"][:100],
                value=cid,
                emoji=meta.get("emoji") or "🛒",
                description=f"{n} productos · {rango}"[:100],
            ))
        super().__init__(
            placeholder="🛒 Elige categoría para ver precios y comprar…",
            options=opts,
            min_values=1,
            max_values=1,
            custom_id="tienda_cat",
        )

    async def callback(self, inter: discord.Interaction):
        cat = self.values[0]
        items = items_por_categoria(cat)
        if not items:
            await inter.response.send_message("No hay productos en esta categoría.", ephemeral=True)
            return
        meta = CATEGORIAS_META.get(cat, {})
        bal = economia.obtener_balance(inter.user.id)
        emb = discord.Embed(
            title=f"{meta.get('emoji','🛒')} {meta.get('nombre', cat)}",
            description=(
                f"Tu saldo: **{MONEDA}{bal:.2f}**\n"
                f"Elige un producto abajo para **comprar 1 unidad**."
            ),
            color=0x2ECC71,
        )
        for iid, d in items[:15]:
            st = d.get("stock", -1)
            st_txt = "∞" if st < 0 else str(st)
            puede = "✅" if bal >= float(d["precio"]) else "❌"
            emb.add_field(
                name=f"{d.get('emoji','')} {d['nombre']} — **{MONEDA}{d['precio']:.2f}** {puede}",
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
                label=f"{d['nombre'][:70]}",
                value=iid,
                emoji=d.get("emoji") or "🛒",
                description=f"Pagar {MONEDA}{d['precio']:.2f} · {(d.get('desc') or '')[:50]}"[:100],
            ))
        super().__init__(
            placeholder="💳 Selecciona qué comprar (se descuenta al elegir)…",
            options=opts,
            min_values=1,
            max_values=1,
        )

    async def callback(self, inter: discord.Interaction):
        ok, msg = comprar(inter.user.id, self.values[0], 1)
        bal = economia.obtener_balance(inter.user.id)
        emb = discord.Embed(
            title="🛒 Compra realizada" if ok else "❌ Compra fallida",
            description=msg,
            color=0x2ECC71 if ok else 0xE74C3C,
        )
        emb.set_footer(text=f"Saldo restante: {MONEDA}{bal:.2f}")
        await inter.response.send_message(embed=emb, ephemeral=True)


class ProductoView(ui.View):
    def __init__(self, cat: str):
        super().__init__(timeout=120)
        self.add_item(ProductoSelect(cat))


class TiendaView(ui.View):
    """Panel permanente: miembros y staff pueden comprar."""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategoriaSelect())

    @ui.button(label="Ver catálogo completo", style=discord.ButtonStyle.primary, emoji="📋", custom_id="tienda_catalogo")
    async def catalogo(self, inter: discord.Interaction, btn: ui.Button):
        await inter.response.send_message(embed=embed_catalogo_completo(), ephemeral=True)

    @ui.button(label="Mi saldo", style=discord.ButtonStyle.secondary, emoji="💰", custom_id="tienda_saldo")
    async def saldo(self, inter: discord.Interaction, btn: ui.Button):
        bal = economia.obtener_balance(inter.user.id)
        await inter.response.send_message(
            f"💰 Tu saldo hospitalario: **{MONEDA}{bal:.2f}**",
            ephemeral=True,
        )

    @ui.button(label="Mi inventario", style=discord.ButtonStyle.secondary, emoji="🎒", custom_id="tienda_inv")
    async def inv(self, inter: discord.Interaction, btn: ui.Button):
        bag = inv_jugador(inter.user.id)
        if not bag:
            await inter.response.send_message(
                "🎒 Inventario vacío. Usa **Bienvenida** o compra en la tienda.",
                ephemeral=True,
            )
            return
        lines = [
            f"• {CATALOGO.get(i, {}).get('emoji','📦')} **{CATALOGO.get(i, {}).get('nombre', i)}** ×{c}"
            for i, c in bag.items()
        ]
        await inter.response.send_message(
            embed=discord.Embed(title="🎒 Tu inventario", description="\n".join(lines), color=0x3498DB),
            ephemeral=True,
        )


def embed_catalogo_completo() -> discord.Embed:
    emb = discord.Embed(
        title="📋 Catálogo completo — precios",
        description="Todos los productos y lo que pagarías al comprar **1 unidad**.",
        color=0x27AE60,
    )
    for cid, meta in sorted(CATEGORIAS_META.items(), key=lambda x: x[1].get("orden", 99)):
        items = items_por_categoria(cid)
        if not items:
            continue
        lines = []
        for _, d in items:
            st = d.get("stock", -1)
            st_txt = "∞" if st < 0 else str(st)
            lines.append(
                f"{d.get('emoji','•')} **{d['nombre']}** — `{MONEDA}{d['precio']:.2f}` (stock {st_txt})"
            )
        texto = "\n".join(lines)
        if len(texto) > 1020:
            texto = texto[:1017] + "…"
        emb.add_field(
            name=f"{meta.get('emoji','')} {meta['nombre']}",
            value=texto,
            inline=False,
        )
    emb.set_footer(text="Elige categoría en el menú del panel para comprar")
    return emb


def embed_tienda() -> discord.Embed:
    cats_lines = []
    for cid, meta in sorted(CATEGORIAS_META.items(), key=lambda x: x[1].get("orden", 99)):
        items = items_por_categoria(cid)
        if not items:
            continue
        precios = [d["precio"] for _, d in items]
        cats_lines.append(
            f"{meta.get('emoji','🛒')} **{meta['nombre']}** — "
            f"{len(items)} ítems · desde **{MONEDA}{min(precios):.2f}**"
        )
    return discord.Embed(
        title="🛒 Tienda del Hospital",
        description=(
            "Panel para **miembros y staff**.\n"
            "1. Elige una **categoría** en el menú\n"
            "2. Revisa el precio y pulsa el producto para **pagar**\n"
            "3. **Ver catálogo completo** lista todos los precios\n\n"
            + "\n".join(cats_lines)
        ),
        color=0x27AE60,
    )


def registrar(bot: commands.Bot) -> None:

    @bot.tree.command(name="tienda", description="Abre la tienda del hospital (precios y compra)")
    async def tienda_cmd(inter: discord.Interaction):
        await inter.response.send_message(embed=embed_tienda(), view=TiendaView(), ephemeral=True)

    @bot.tree.command(name="panel_tienda", description="Publica el panel permanente de la tienda")
    @app_commands.describe(canal="Canal donde publicar el panel")
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
        await inter.response.send_message(f"✅ Panel tienda en {dest.mention}", ephemeral=True)

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
                title="🎁 Bienvenida",
                description=msg,
                color=0x2ECC71 if ok else 0xF39C12,
            ),
            ephemeral=True,
        )

    @bot.tree.command(name="catalogo_tienda", description="Ver todos los precios del catálogo")
    async def catalogo_cmd(inter: discord.Interaction):
        await inter.response.send_message(embed=embed_catalogo_completo(), ephemeral=True)

    bot.add_view(TiendaView())
    print("[tienda] OK")
