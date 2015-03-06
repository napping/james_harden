def get_chunks(alignment, translation, reference):
    current_chunk = 0
    chunks = 1
    # fugly code =/
    remaining_alignment = alignment
    for i in range(len(translation) - 1):
        this_align = [mapping for mapping in remaining_alignment if mapping[0] == translation[i]][0]
        next_align = [mapping for mapping in remaining_alignment if mapping[0] == translation[i+1]][0]
        print this_align, next_align

        if len(this_align) == 0 or None in this_align or None in next_align:
            continue

        if (reference.index(this_align[1]) + 1) != (reference.index(next_align[1])):
            chunks += 1
        
    return chunks
