# Crossed-book investigation

Raw MBO applied with the existing `LimitOrderBook` rules. The replay engine was not modified.
A wide episode is a bid at least 10 index points above the ask. One-tick crosses are not listed.

## Conclusion

The 25 crossed snapshot rows are in the raw feed. The reconstruction is correct, so those rows stay.

On every burst boundary, including the uncrossed second before and the uncrossed second after, the replayed bid, ask, and top-of-book size match the stored parquet. Mismatches: 0. Instrument in each window: 42004177 only. No `F_MAYBE_BAD_BOOK`, no `F_BAD_TS_RECV`, no snapshot, no clear. No timestamp reversal. No same-timestamp sequence reversal inside the window. No orphan cancel or modify.

What the feed does, in each burst, is publish Add records (and, on 2026-07-13, a Modify) that place ask orders below the best bid, while other Add records place bid orders above the best ask. Many price levels sit between those two prices. The orders were born in that same second, not left over from the opening snapshot. The book is crossed at the one-second clock for 15, 5, and 5 seconds, then an ask cancel brings it back to bid < ask. The next stored second is uncrossed and matches.

This is not a clock bug, a same-timestamp ordering bug, a snapshot artifact, or a missed cancel among the records we received. The 10-point "opener" in the log below is the event that pushed an already-developing cross through 10 points. On 2026-07-10 and 2026-08-11 the book was already crossed by less than 10 points before that event. The second boundary before each burst is a normal positive spread.

Two earlier wide episodes on 2026-07-10, maximum 20 points, ended before this burst and do not appear in the snapshot store. 2026-07-13 and 2026-08-11 had none before the burst. Action `N` is Databento `NONE` and does not change the book; the engine already ignores it.

## 2026-07-10

- Flag constants used: {'F_MAYBE_BAD_BOOK': 4, 'F_BAD_TS_RECV': 8, 'F_SNAPSHOT': 32, 'F_LAST': 128}
- Instrument ids in the ±2s window: [42004177]
- Action counts in the ±2s window: {'A': 3818, 'C': 5191, 'M': 3041, 'T': 685, 'F': 1277, 'R': 0, 'N': 130}
- Flags in the ±2s window: {'maybe_bad_book': 0, 'bad_ts_recv': 0, 'snapshot': 0, 'clear': 0}
- Timestamp reversals from file start through the window: 0
- Same-timestamp sequence reversals inside the ±2s window: 0
- Orphan cancels by the end of the window: 0
- Orphan modifies by the end of the window: 0
- Wide episodes (bid at least 10 points through ask) before the window: 2
- Largest such pre-window width, points: 20.0
- Wide episodes that overlap the burst window: 2
- Wide episodes closed before the window ended: 4

Wide episode start=1783693961418427237 end=1783693971418000000 max_width_points=92.5 duration_ns=9999572763
- opener: ts=1783693961418427237 seq=496272840 A A px=29913.5 sz=1 order=6879487776905 flags=0 iid=42004177 book 29924.5/29914.75 -> 29924.5/29913.5 (born incremental ts=1783693961418427237 seq=496272840 iid=42004177 side=A px=29913.5 sz=1)
- widest: ts=1783693967209090833 seq=496331331 A A px=29855.0 sz=1 order=6879487887026 flags=128 iid=42004177 book 29947.5/29856.0 -> 29947.5/29855.0 (born incremental ts=1783693967209090833 seq=496331331 iid=42004177 side=A px=29855.0 sz=1)
- closer: ts=1783693971418000000 seq=496365107 C A px=29880.75 sz=1 order=6879486563014 flags=0 iid=42004177 book 29890.75/29880.75 -> 29890.75/29881.0 (born incremental ts=1783693493004237451 seq=494124520 iid=42004177 side=A px=29900.25 sz=1)

Wide episode start=1783693971606487941 end=1783693976606000000 max_width_points=146.75 duration_ns=4999512059
- opener: ts=1783693971606487941 seq=496367882 A A px=29840.0 sz=1 order=6879487331886 flags=0 iid=42004177 book 29850.5/29841.75 -> 29850.5/29840.0 (born incremental ts=1783693971606487941 seq=496367882 iid=42004177 side=A px=29840.0 sz=1)
- widest: ts=1783693975879353907 seq=496398072 A A px=29818.0 sz=5 order=6879487936978 flags=128 iid=42004177 book 29964.75/29832.5 -> 29964.75/29818.0 (born incremental ts=1783693975879353907 seq=496398072 iid=42004177 side=A px=29818.0 sz=5)
- closer: ts=1783693976606000000 seq=496403185 C A px=29840.0 sz=1 order=6879487331886 flags=0 iid=42004177 book 29850.0/29840.0 -> 29850.0/29841.75 (born incremental ts=1783693971606487941 seq=496367882 iid=42004177 side=A px=29840.0 sz=1)

Snapshot-clock book versus stored parquet. Neighbors one second outside the burst are included.

- ts=1783693961000000000 reconstructed bid=29956.0 sz=1 ask=29956.75 sz=2 stored bid=29956.0 sz=1 ask=29956.75 sz=2 match=True crossed=False
- ts=1783693962000000000 reconstructed bid=29950.25 sz=1 ask=29910.0 sz=1 stored bid=29950.25 sz=1 ask=29910.0 sz=1 match=True crossed=True
- ts=1783693963000000000 reconstructed bid=29950.25 sz=1 ask=29888.5 sz=1 stored bid=29950.25 sz=1 ask=29888.5 sz=1 match=True crossed=True
- ts=1783693964000000000 reconstructed bid=29934.25 sz=3 ask=29879.75 sz=1 stored bid=29934.25 sz=3 ask=29879.75 sz=1 match=True crossed=True
- ts=1783693965000000000 reconstructed bid=29934.25 sz=1 ask=29868.0 sz=1 stored bid=29934.25 sz=1 ask=29868.0 sz=1 match=True crossed=True
- ts=1783693966000000000 reconstructed bid=29947.5 sz=1 ask=29866.0 sz=5 stored bid=29947.5 sz=1 ask=29866.0 sz=5 match=True crossed=True
- ts=1783693967000000000 reconstructed bid=29947.5 sz=1 ask=29864.5 sz=1 stored bid=29947.5 sz=1 ask=29864.5 sz=1 match=True crossed=True
- ts=1783693968000000000 reconstructed bid=29947.5 sz=1 ask=29855.0 sz=1 stored bid=29947.5 sz=1 ask=29855.0 sz=1 match=True crossed=True
- ts=1783693969000000000 reconstructed bid=29947.5 sz=1 ask=29866.0 sz=5 stored bid=29947.5 sz=1 ask=29866.0 sz=5 match=True crossed=True
- ts=1783693970000000000 reconstructed bid=29947.5 sz=1 ask=29866.0 sz=5 stored bid=29947.5 sz=1 ask=29866.0 sz=5 match=True crossed=True
- ts=1783693971000000000 reconstructed bid=29947.5 sz=1 ask=29875.0 sz=1 stored bid=29947.5 sz=1 ask=29875.0 sz=1 match=True crossed=True
- ts=1783693972000000000 reconstructed bid=29916.0 sz=1 ask=29838.25 sz=2 stored bid=29916.0 sz=1 ask=29838.25 sz=2 match=True crossed=True
- ts=1783693973000000000 reconstructed bid=29951.25 sz=1 ask=29838.25 sz=2 stored bid=29951.25 sz=1 ask=29838.25 sz=2 match=True crossed=True
- ts=1783693974000000000 reconstructed bid=29951.25 sz=1 ask=29832.5 sz=2 stored bid=29951.25 sz=1 ask=29832.5 sz=2 match=True crossed=True
- ts=1783693975000000000 reconstructed bid=29964.75 sz=1 ask=29832.5 sz=2 stored bid=29964.75 sz=1 ask=29832.5 sz=2 match=True crossed=True
- ts=1783693976000000000 reconstructed bid=29964.75 sz=2 ask=29818.0 sz=5 stored bid=29964.75 sz=2 ask=29818.0 sz=5 match=True crossed=True
- ts=1783693977000000000 reconstructed bid=29824.75 sz=1 ask=29828.25 sz=2 stored bid=29824.75 sz=1 ask=29828.25 sz=2 match=True crossed=False

Stored-versus-replay mismatches on these boundaries: 0

Orders at the first crossed snapshot boundary ts=1783693962000000000:
Bids above the ask, best first:
- bid level px=29950.25 sz=1 orders=[(6879487838758, 1, 'born incremental ts=1783693961419247539 seq=496273199 iid=42004177 side=B px=29950.25 sz=1')]
- bid level px=29934.25 sz=3 orders=[(6879487844204, 1, 'born incremental ts=1783693961797860221 seq=496278649 iid=42004177 side=B px=29934.25 sz=1'), (6879487847237, 2, 'born incremental ts=1783693961995036105 seq=496281082 iid=42004177 side=B px=29934.25 sz=2')]
- bid level px=29925.75 sz=1 orders=[(6879487840921, 1, 'born incremental ts=1783693961434116365 seq=496275004 iid=42004177 side=B px=29925.75 sz=1')]
- bid level px=29924.25 sz=1 orders=[(6879487629602, 1, 'born incremental ts=1783693875106092359 seq=495911588 iid=42004177 side=B px=29914.25 sz=1')]
- bid level px=29924.0 sz=1 orders=[(6879487702000, 1, 'born incremental ts=1783693907469479421 seq=496040514 iid=42004177 side=B px=29924.0 sz=1')]
- bid level px=29923.5 sz=1 orders=[(6879487842514, 1, 'born incremental ts=1783693961511086811 seq=496277161 iid=42004177 side=B px=29923.5 sz=1')]
- bid level px=29921.5 sz=1 orders=[(6879487717735, 1, 'born incremental ts=1783693915035626977 seq=496069250 iid=42004177 side=B px=29921.5 sz=1')]
- bid level px=29921.0 sz=1 orders=[(6879487631406, 1, 'born incremental ts=1783693875919381865 seq=495914834 iid=42004177 side=B px=29911.25 sz=1')]
- bid level px=29920.25 sz=1 orders=[(6879487790811, 1, 'born incremental ts=1783693943305686421 seq=496194846 iid=42004177 side=B px=29920.25 sz=1')]
- bid level px=29920.0 sz=52 orders=[(6879487681980, 40, 'born incremental ts=1783693898543786429 seq=496004496 iid=42004177 side=B px=29921.25 sz=40'), (6879487697362, 1, 'born incremental ts=1783693905250412969 seq=496031729 iid=42004177 side=B px=29920.0 sz=1'), (6879487730357, 2, 'born incremental ts=1783693920917346643 seq=496091311 iid=42004177 side=B px=29920.0 sz=2'), (6879487804523, 8, 'born incremental ts=1783693946092588643 seq=496215940 iid=42004177 side=B px=29920.0 sz=8'), (6879487805525, 1, 'born incremental ts=1783693946511743027 seq=496217728 iid=42004177 side=B px=29920.0 sz=1')]
- bid level px=29919.75 sz=1 orders=[(6879487649820, 1, 'born incremental ts=1783693884348533651 seq=495947952 iid=42004177 side=B px=29919.75 sz=1')]
- bid level px=29918.0 sz=1 orders=[(6879487705627, 1, 'born incremental ts=1783693909438520261 seq=496047399 iid=42004177 side=B px=29918.0 sz=1')]
- best ask px=29910.0 sz=1 orders=[(6879487777554, 1, 'born incremental ts=1783693961418427237 seq=496272840 iid=42004177 side=A px=29910.0 sz=1')]
- next ask levels: [29910.0, 29910.25, 29910.75, 29912.0]
- next bid levels from the top: [29950.25, 29934.25, 29925.75, 29924.25]

Orders at the last crossed snapshot boundary ts=1783693976000000000:
Bids above the ask, best first:
- bid level px=29964.75 sz=2 orders=[(6879487930497, 1, 'born incremental ts=1783693974206322425 seq=496387897 iid=42004177 side=B px=29964.75 sz=1'), (6879487934581, 1, 'born incremental ts=1783693975126615783 seq=496394312 iid=42004177 side=B px=29964.75 sz=1')]
- bid level px=29927.0 sz=1 orders=[(6879487935437, 1, 'born incremental ts=1783693975355752073 seq=496395694 iid=42004177 side=B px=29927.0 sz=1')]
- bid level px=29916.0 sz=1 orders=[(6879487917921, 1, 'born incremental ts=1783693971936625965 seq=496370902 iid=42004177 side=B px=29916.0 sz=1')]
- bid level px=29902.0 sz=1 orders=[(6879487916735, 1, 'born incremental ts=1783693971759003577 seq=496369643 iid=42004177 side=B px=29902.0 sz=1')]
- bid level px=29876.75 sz=1 orders=[(6879487917089, 1, 'born incremental ts=1783693971824496601 seq=496370036 iid=42004177 side=B px=29876.75 sz=1')]
- bid level px=29864.75 sz=1 orders=[(6879487935593, 1, 'born incremental ts=1783693975422273325 seq=496395969 iid=42004177 side=B px=29864.75 sz=1')]
- bid level px=29851.25 sz=1 orders=[(6879487932365, 1, 'born incremental ts=1783693974658916663 seq=496391207 iid=42004177 side=B px=29851.25 sz=1')]
- bid level px=29850.5 sz=2 orders=[(6879486448597, 2, 'born incremental ts=1783693448666408943 seq=493920636 iid=42004177 side=B px=29850.5 sz=2')]
- bid level px=29850.25 sz=4 orders=[(6879486787176, 1, 'born incremental ts=1783693565642619795 seq=494512973 iid=42004177 side=B px=29850.25 sz=1'), (6879486989435, 2, 'born incremental ts=1783693641588829449 seq=494850141 iid=42004177 side=B px=29850.25 sz=2'), (6879487557668, 1, 'born incremental ts=1783693847944948489 seq=495790573 iid=42004177 side=B px=29850.25 sz=1')]
- bid level px=29850.0 sz=9 orders=[(6879481507738, 1, 'born incremental ts=1783691568019545781 seq=485153396 iid=42004177 side=B px=29750.0 sz=1'), (6879485662296, 1, 'born incremental ts=1783693182032486829 seq=492607979 iid=42004177 side=B px=29800.0 sz=1'), (6879486176500, 1, 'born incremental ts=1783693353691943521 seq=493461267 iid=42004177 side=B px=29850.0 sz=1'), (6879486368697, 1, 'born incremental ts=1783693422681535701 seq=493786778 iid=42004177 side=B px=29850.0 sz=1'), (6879486406674, 1, 'born incremental ts=1783693434536648141 seq=493850613 iid=42004177 side=B px=29850.0 sz=1'), (6879486965885, 1, 'born incremental ts=1783693631473698845 seq=494809359 iid=42004177 side=B px=29850.0 sz=1'), (6879486983690, 1, 'born incremental ts=1783693638412844713 seq=494840797 iid=42004177 side=B px=29850.0 sz=1'), (6879487495351, 1, 'born incremental ts=1783693824443459575 seq=495683649 iid=42004177 side=B px=29850.0 sz=1')]
- bid level px=29849.5 sz=1 orders=[(6879487340242, 1, 'born incremental ts=1783693774964796469 seq=495432898 iid=42004177 side=B px=29849.5 sz=1')]
- bid level px=29849.0 sz=1 orders=[(6879486162423, 1, 'born incremental ts=1783693348550255571 seq=493436720 iid=42004177 side=B px=29849.0 sz=1')]
- best ask px=29818.0 sz=5 orders=[(6879487936978, 5, 'born incremental ts=1783693975879353907 seq=496398072 iid=42004177 side=A px=29818.0 sz=5')]
- next ask levels: [29818.0, 29832.5, 29838.25, 29840.0]
- next bid levels from the top: [29964.75, 29927.0, 29916.0, 29902.0]

## 2026-07-13

- Flag constants used: {'F_MAYBE_BAD_BOOK': 4, 'F_BAD_TS_RECV': 8, 'F_SNAPSHOT': 32, 'F_LAST': 128}
- Instrument ids in the ±2s window: [42004177]
- Action counts in the ±2s window: {'A': 5437, 'C': 6858, 'M': 3236, 'T': 1127, 'F': 1655, 'R': 0, 'N': 236}
- Flags in the ±2s window: {'maybe_bad_book': 0, 'bad_ts_recv': 0, 'snapshot': 0, 'clear': 0}
- Timestamp reversals from file start through the window: 0
- Same-timestamp sequence reversals inside the ±2s window: 0
- Orphan cancels by the end of the window: 0
- Orphan modifies by the end of the window: 0
- Wide episodes (bid at least 10 points through ask) before the window: 0
- Largest such pre-window width, points: 0.0
- Wide episodes that overlap the burst window: 1
- Wide episodes closed before the window ended: 1

Wide episode start=1783952205300968853 end=1783952210300000000 max_width_points=120.75 duration_ns=4999031147
- opener: ts=1783952205300968853 seq=52238251 A A px=29541.5 sz=1 order=6879541837832 flags=0 iid=42004177 book 29555.0/29558.75 -> 29555.0/29541.5 (born incremental ts=1783952205300968853 seq=52238251 iid=42004177 side=A px=29541.5 sz=1)
- widest: ts=1783952210296774473 seq=52289696 M A px=29528.25 sz=1 order=6879541398989 flags=128 iid=42004177 book 29649.0/29528.5 -> 29649.0/29528.25 (born incremental ts=1783952038439094385 seq=51505369 iid=42004177 side=A px=29643.5 sz=1)
- closer: ts=1783952210300000000 seq=52289752 C A px=29534.0 sz=1 order=6879541457635 flags=0 iid=42004177 book 29544.0/29534.0 -> 29544.0/29534.25 (born incremental ts=1783952065195922345 seq=51612926 iid=42004177 side=A px=29651.5 sz=1)

Snapshot-clock book versus stored parquet. Neighbors one second outside the burst are included.

- ts=1783952205000000000 reconstructed bid=29570.75 sz=1 ask=29575.75 sz=2 stored bid=29570.75 sz=1 ask=29575.75 sz=2 match=True crossed=False
- ts=1783952206000000000 reconstructed bid=29627.75 sz=1 ask=29541.5 sz=1 stored bid=29627.75 sz=1 ask=29541.5 sz=1 match=True crossed=True
- ts=1783952207000000000 reconstructed bid=29649.0 sz=10 ask=29541.5 sz=1 stored bid=29649.0 sz=10 ask=29541.5 sz=1 match=True crossed=True
- ts=1783952208000000000 reconstructed bid=29649.0 sz=10 ask=29541.5 sz=1 stored bid=29649.0 sz=10 ask=29541.5 sz=1 match=True crossed=True
- ts=1783952209000000000 reconstructed bid=29649.0 sz=10 ask=29538.5 sz=1 stored bid=29649.0 sz=10 ask=29538.5 sz=1 match=True crossed=True
- ts=1783952210000000000 reconstructed bid=29649.0 sz=10 ask=29532.5 sz=1 stored bid=29649.0 sz=10 ask=29532.5 sz=1 match=True crossed=True
- ts=1783952211000000000 reconstructed bid=29503.0 sz=4 ask=29508.75 sz=1 stored bid=29503.0 sz=4 ask=29508.75 sz=1 match=True crossed=False

Stored-versus-replay mismatches on these boundaries: 0

Orders at the first crossed snapshot boundary ts=1783952206000000000:
Bids above the ask, best first:
- bid level px=29627.75 sz=1 orders=[(6879541841917, 1, 'born incremental ts=1783952205535633255 seq=52242351 iid=42004177 side=B px=29627.75 sz=1')]
- bid level px=29570.0 sz=10 orders=[(6879541842209, 10, 'born incremental ts=1783952205546842903 seq=52242572 iid=42004177 side=B px=29570.0 sz=10')]
- bid level px=29559.75 sz=1 orders=[(6879541838438, 1, 'born incremental ts=1783952205337101343 seq=52239121 iid=42004177 side=B px=29559.75 sz=1')]
- bid level px=29555.0 sz=2 orders=[(6879531809274, 1, 'born incremental ts=1783949630741734533 seq=35750860 iid=42004177 side=B px=29500.0 sz=1'), (6879541316509, 1, 'born incremental ts=1783952003067454595 seq=51367361 iid=42004177 side=B px=29555.0 sz=1')]
- bid level px=29553.5 sz=1 orders=[(6879539390568, 1, 'born incremental ts=1783951370744289603 seq=48085353 iid=42004177 side=B px=29553.5 sz=1')]
- bid level px=29552.5 sz=1 orders=[(6879540259307, 1, 'born incremental ts=1783951640394913793 seq=49575344 iid=42004177 side=B px=29552.5 sz=1')]
- bid level px=29552.25 sz=3 orders=[(6879538330841, 3, 'born incremental ts=1783951104065894815 seq=46349190 iid=42004177 side=B px=29552.25 sz=3')]
- bid level px=29551.5 sz=2 orders=[(6879541839015, 2, 'born incremental ts=1783952205377929903 seq=52239832 iid=42004177 side=B px=29551.5 sz=2')]
- bid level px=29551.25 sz=2 orders=[(6879538064386, 1, 'born incremental ts=1783951028372429597 seq=45903912 iid=42004177 side=B px=29551.25 sz=1'), (6879541838858, 1, 'born incremental ts=1783952205359516069 seq=52239596 iid=42004177 side=B px=29551.25 sz=1')]
- bid level px=29550.5 sz=2 orders=[(6879539350593, 1, 'born incremental ts=1783951360247291449 seq=48016270 iid=42004177 side=B px=29550.5 sz=1'), (6879541193316, 1, 'born incremental ts=1783951954517954197 seq=51154923 iid=42004177 side=B px=29618.5 sz=1')]
- bid level px=29550.0 sz=21 orders=[(6879538259418, 1, 'born incremental ts=1783951084850138681 seq=46233144 iid=42004177 side=B px=29550.0 sz=1'), (6879538315126, 1, 'born incremental ts=1783951099537914763 seq=46323258 iid=42004177 side=B px=29550.0 sz=1'), (6879538418845, 1, 'born incremental ts=1783951132805773505 seq=46497917 iid=42004177 side=B px=29550.0 sz=1'), (6879539443158, 1, 'born incremental ts=1783951384777772755 seq=48177633 iid=42004177 side=B px=29550.0 sz=1'), (6879539868455, 1, 'born incremental ts=1783951517809010823 seq=48915039 iid=42004177 side=B px=29550.0 sz=1'), (6879540092645, 1, 'born incremental ts=1783951587666627485 seq=49290730 iid=42004177 side=B px=29550.0 sz=1'), (6879540098738, 1, 'born incremental ts=1783951589340225411 seq=49301058 iid=42004177 side=B px=29550.0 sz=1'), (6879540380882, 4, 'born incremental ts=1783951682919523837 seq=49777152 iid=42004177 side=B px=29550.0 sz=4')]
- bid level px=29549.0 sz=1 orders=[(6879541542054, 1, 'born incremental ts=1783952102771700271 seq=51756654 iid=42004177 side=B px=29549.0 sz=1')]
- best ask px=29541.5 sz=1 orders=[(6879541837832, 1, 'born incremental ts=1783952205300968853 seq=52238251 iid=42004177 side=A px=29541.5 sz=1')]
- next ask levels: [29541.5, 29555.25, 29565.0, 29566.0]
- next bid levels from the top: [29627.75, 29570.0, 29559.75, 29555.0]

Orders at the last crossed snapshot boundary ts=1783952210000000000:
Bids above the ask, best first:
- bid level px=29649.0 sz=10 orders=[(6879541849462, 10, 'born incremental ts=1783952206337212311 seq=52252629 iid=42004177 side=B px=29649.0 sz=10')]
- bid level px=29645.0 sz=1 orders=[(6879541858531, 1, 'born incremental ts=1783952207857094879 seq=52268163 iid=42004177 side=B px=29645.0 sz=1')]
- bid level px=29627.75 sz=1 orders=[(6879541841917, 1, 'born incremental ts=1783952205535633255 seq=52242351 iid=42004177 side=B px=29627.75 sz=1')]
- bid level px=29607.0 sz=1 orders=[(6879541855710, 1, 'born incremental ts=1783952207440978597 seq=52263255 iid=42004177 side=B px=29607.0 sz=1')]
- bid level px=29575.75 sz=1 orders=[(6879541857970, 1, 'born incremental ts=1783952207715681593 seq=52267022 iid=42004177 side=B px=29575.75 sz=1')]
- bid level px=29575.0 sz=1 orders=[(6879541848357, 1, 'born incremental ts=1783952206152241611 seq=52250648 iid=42004177 side=B px=29575.0 sz=1')]
- bid level px=29570.25 sz=1 orders=[(6879541853161, 1, 'born incremental ts=1783952207067727671 seq=52259477 iid=42004177 side=B px=29570.25 sz=1')]
- bid level px=29570.0 sz=10 orders=[(6879541842209, 10, 'born incremental ts=1783952205546842903 seq=52242572 iid=42004177 side=B px=29570.0 sz=10')]
- bid level px=29562.0 sz=12 orders=[(6879541869377, 12, 'born incremental ts=1783952209999010317 seq=52287395 iid=42004177 side=B px=29562.0 sz=12')]
- bid level px=29555.0 sz=2 orders=[(6879531809274, 1, 'born incremental ts=1783949630741734533 seq=35750860 iid=42004177 side=B px=29500.0 sz=1'), (6879541316509, 1, 'born incremental ts=1783952003067454595 seq=51367361 iid=42004177 side=B px=29555.0 sz=1')]
- bid level px=29553.5 sz=1 orders=[(6879539390568, 1, 'born incremental ts=1783951370744289603 seq=48085353 iid=42004177 side=B px=29553.5 sz=1')]
- bid level px=29552.5 sz=1 orders=[(6879540259307, 1, 'born incremental ts=1783951640394913793 seq=49575344 iid=42004177 side=B px=29552.5 sz=1')]
- best ask px=29532.5 sz=1 orders=[(6879540610724, 1, 'born incremental ts=1783951759797572263 seq=50170101 iid=42004177 side=A px=29621.0 sz=1')]
- next ask levels: [29532.5, 29532.75, 29533.0, 29533.25]
- next bid levels from the top: [29649.0, 29645.0, 29627.75, 29607.0]

## 2026-08-11

- Flag constants used: {'F_MAYBE_BAD_BOOK': 4, 'F_BAD_TS_RECV': 8, 'F_SNAPSHOT': 32, 'F_LAST': 128}
- Instrument ids in the ±2s window: [42004177]
- Action counts in the ±2s window: {'A': 4127, 'C': 5194, 'M': 1877, 'T': 965, 'F': 1530, 'R': 0, 'N': 203}
- Flags in the ±2s window: {'maybe_bad_book': 0, 'bad_ts_recv': 0, 'snapshot': 0, 'clear': 0}
- Timestamp reversals from file start through the window: 0
- Same-timestamp sequence reversals inside the ±2s window: 0
- Orphan cancels by the end of the window: 0
- Orphan modifies by the end of the window: 0
- Wide episodes (bid at least 10 points through ask) before the window: 0
- Largest such pre-window width, points: 0.0
- Wide episodes that overlap the burst window: 1
- Wide episodes closed before the window ended: 1

Wide episode start=1786455961273612683 end=1786455966273000000 max_width_points=60.25 duration_ns=4999387317
- opener: ts=1786455961273612683 seq=105755217 A A px=29625.0 sz=1 order=6880917430397 flags=0 iid=42004177 book 29636.5/29629.25 -> 29636.5/29625.0 (born incremental ts=1786455961273612683 seq=105755217 iid=42004177 side=A px=29625.0 sz=1)
- widest: ts=1786455961939422423 seq=105762284 A B px=29683.0 sz=1 order=6880917802272 flags=128 iid=42004177 book 29682.75/29622.75 -> 29683.0/29622.75 (born incremental ts=1786455961939422423 seq=105762284 iid=42004177 side=B px=29683.0 sz=1)
- closer: ts=1786455966273000000 seq=105778497 C A px=29636.0 sz=1 order=6880917803894 flags=0 iid=42004177 book 29646.75/29636.0 -> 29646.75/29640.0 (born incremental ts=1786455962131428889 seq=105764355 iid=42004177 side=A px=29636.0 sz=1)

Snapshot-clock book versus stored parquet. Neighbors one second outside the burst are included.

- ts=1786455961000000000 reconstructed bid=29680.75 sz=2 ask=29681.5 sz=1 stored bid=29680.75 sz=2 ask=29681.5 sz=1 match=True crossed=False
- ts=1786455962000000000 reconstructed bid=29683.0 sz=1 ask=29622.75 sz=2 stored bid=29683.0 sz=1 ask=29622.75 sz=2 match=True crossed=True
- ts=1786455963000000000 reconstructed bid=29683.0 sz=1 ask=29622.75 sz=2 stored bid=29683.0 sz=1 ask=29622.75 sz=2 match=True crossed=True
- ts=1786455964000000000 reconstructed bid=29683.0 sz=8 ask=29622.75 sz=2 stored bid=29683.0 sz=8 ask=29622.75 sz=2 match=True crossed=True
- ts=1786455965000000000 reconstructed bid=29683.0 sz=8 ask=29622.75 sz=2 stored bid=29683.0 sz=8 ask=29622.75 sz=2 match=True crossed=True
- ts=1786455966000000000 reconstructed bid=29683.0 sz=8 ask=29622.75 sz=2 stored bid=29683.0 sz=8 ask=29622.75 sz=2 match=True crossed=True
- ts=1786455967000000000 reconstructed bid=29659.25 sz=4 ask=29660.0 sz=2 stored bid=29659.25 sz=4 ask=29660.0 sz=2 match=True crossed=False

Stored-versus-replay mismatches on these boundaries: 0

Orders at the first crossed snapshot boundary ts=1786455962000000000:
Bids above the ask, best first:
- bid level px=29683.0 sz=1 orders=[(6880917802272, 1, 'born incremental ts=1786455961939422423 seq=105762284 iid=42004177 side=B px=29683.0 sz=1')]
- bid level px=29682.75 sz=1 orders=[(6880917801095, 1, 'born incremental ts=1786455961831313295 seq=105761155 iid=42004177 side=B px=29682.75 sz=1')]
- bid level px=29681.75 sz=1 orders=[(6880917802214, 1, 'born incremental ts=1786455961933173677 seq=105762187 iid=42004177 side=B px=29681.75 sz=1')]
- bid level px=29679.0 sz=1 orders=[(6880917801928, 1, 'born incremental ts=1786455961920130125 seq=105761975 iid=42004177 side=B px=29679.0 sz=1')]
- bid level px=29661.25 sz=50 orders=[(6880917798073, 50, 'born incremental ts=1786455961290882199 seq=105755876 iid=42004177 side=B px=29661.25 sz=50')]
- bid level px=29648.75 sz=1 orders=[(6880917797648, 1, 'born incremental ts=1786455961287128583 seq=105755416 iid=42004177 side=B px=29648.75 sz=1')]
- bid level px=29647.0 sz=2 orders=[(6880917801367, 2, 'born incremental ts=1786455961872960999 seq=105761454 iid=42004177 side=B px=29647.0 sz=2')]
- bid level px=29642.0 sz=1 orders=[(6880917797992, 1, 'born incremental ts=1786455961290112507 seq=105755701 iid=42004177 side=B px=29642.0 sz=1')]
- bid level px=29639.75 sz=1 orders=[(6880917802691, 1, 'born incremental ts=1786455961988767081 seq=105762800 iid=42004177 side=B px=29639.75 sz=1')]
- bid level px=29639.5 sz=1 orders=[(6880917801955, 1, 'born incremental ts=1786455961922530977 seq=105762003 iid=42004177 side=B px=29639.5 sz=1')]
- bid level px=29639.25 sz=1 orders=[(6880917801488, 1, 'born incremental ts=1786455961890413787 seq=105761579 iid=42004177 side=B px=29639.25 sz=1')]
- bid level px=29639.0 sz=1 orders=[(6880917801647, 1, 'born incremental ts=1786455961902459139 seq=105761734 iid=42004177 side=B px=29639.0 sz=1')]
- best ask px=29622.75 sz=2 orders=[(6880915335630, 1, 'born incremental ts=1786455961273612683 seq=105755217 iid=42004177 side=A px=29622.75 sz=1'), (6880917801495, 1, 'born incremental ts=1786455961891003623 seq=105761596 iid=42004177 side=A px=29622.75 sz=1')]
- next ask levels: [29622.75, 29624.0, 29625.0, 29629.25]
- next bid levels from the top: [29683.0, 29682.75, 29681.75, 29679.0]

Orders at the last crossed snapshot boundary ts=1786455966000000000:
Bids above the ask, best first:
- bid level px=29683.0 sz=8 orders=[(6880917802272, 1, 'born incremental ts=1786455961939422423 seq=105762284 iid=42004177 side=B px=29683.0 sz=1'), (6880917807004, 1, 'born incremental ts=1786455963072075491 seq=105768720 iid=42004177 side=B px=29683.0 sz=1'), (6880917807138, 1, 'born incremental ts=1786455963075729337 seq=105768800 iid=42004177 side=B px=29683.0 sz=1'), (6880917807339, 1, 'born incremental ts=1786455963129064921 seq=105769155 iid=42004177 side=B px=29683.0 sz=1'), (6880917807357, 1, 'born incremental ts=1786455963132848477 seq=105769186 iid=42004177 side=B px=29683.0 sz=1'), (6880917807368, 1, 'born incremental ts=1786455963136901935 seq=105769211 iid=42004177 side=B px=29683.0 sz=1'), (6880917807414, 1, 'born incremental ts=1786455963140477373 seq=105769252 iid=42004177 side=B px=29683.0 sz=1'), (6880917807435, 1, 'born incremental ts=1786455963144642703 seq=105769305 iid=42004177 side=B px=29683.0 sz=1')]
- bid level px=29682.75 sz=1 orders=[(6880917801095, 1, 'born incremental ts=1786455961831313295 seq=105761155 iid=42004177 side=B px=29682.75 sz=1')]
- bid level px=29680.25 sz=1 orders=[(6880917808743, 1, 'born incremental ts=1786455963745614897 seq=105771103 iid=42004177 side=B px=29680.25 sz=1')]
- bid level px=29679.0 sz=1 orders=[(6880917801928, 1, 'born incremental ts=1786455961920130125 seq=105761975 iid=42004177 side=B px=29679.0 sz=1')]
- bid level px=29672.25 sz=2 orders=[(6880917811025, 2, 'born incremental ts=1786455965187376243 seq=105774892 iid=42004177 side=B px=29672.25 sz=2')]
- bid level px=29662.5 sz=2 orders=[(6880917812048, 2, 'born incremental ts=1786455965852566479 seq=105776511 iid=42004177 side=B px=29662.5 sz=2')]
- bid level px=29661.25 sz=50 orders=[(6880917798073, 50, 'born incremental ts=1786455961290882199 seq=105755876 iid=42004177 side=B px=29661.25 sz=50')]
- bid level px=29658.5 sz=1 orders=[(6880917808692, 1, 'born incremental ts=1786455963711187147 seq=105771035 iid=42004177 side=B px=29658.5 sz=1')]
- bid level px=29658.0 sz=1 orders=[(6880917811936, 1, 'born incremental ts=1786455965705397943 seq=105776316 iid=42004177 side=B px=29658.0 sz=1')]
- bid level px=29657.0 sz=2 orders=[(6880917809614, 1, 'born incremental ts=1786455964253170107 seq=105772791 iid=42004177 side=B px=29657.0 sz=1'), (6880917810255, 1, 'born incremental ts=1786455964726633247 seq=105773808 iid=42004177 side=B px=29657.0 sz=1')]
- bid level px=29656.25 sz=1 orders=[(6880917811312, 1, 'born incremental ts=1786455965467727757 seq=105775341 iid=42004177 side=B px=29656.25 sz=1')]
- bid level px=29656.0 sz=1 orders=[(6880917812324, 1, 'born incremental ts=1786455965992885471 seq=105776968 iid=42004177 side=B px=29656.0 sz=1')]
- best ask px=29622.75 sz=2 orders=[(6880915335630, 1, 'born incremental ts=1786455961273612683 seq=105755217 iid=42004177 side=A px=29622.75 sz=1'), (6880917811081, 1, 'born incremental ts=1786455965243597977 seq=105774951 iid=42004177 side=A px=29622.75 sz=1')]
- next ask levels: [29622.75, 29624.0, 29625.0, 29626.5]
- next bid levels from the top: [29683.0, 29682.75, 29680.25, 29679.0]
